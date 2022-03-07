import time
import requests
import logging
import bs4


class Adapter:

    _s_github = requests.session()
    _s_github.headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36'
    }
    _s_gitea = requests.session()
    _s_gitea.headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        'Accept-Language': 'zh',
        'Content-Type': 'application/x-www-form-urlencoded',
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36'
    }

    _repository_list = []

    _logger = logging.getLogger('main.common')

    def __init__(self, gitea_url: str, github_url: str) -> None:
        self._gitea_url = gitea_url
        self._github_url = github_url

    def Collect(self, github_user, github_proxy: dict = None):
        self._s_github.proxies = {'http': github_proxy, 'https': github_proxy} if github_proxy else {}
        self._logger.info('Github proxy: %s' % github_proxy)
        star_url = '%s/%s?tab=stars' % (self._github_url, github_user)
        self._logger.info('User star url: %s' % star_url)
        while True:
            try:
                r = self._s_github.get(star_url)
                bs4.BeautifulSoup(r.text).find('Next')
                for item in bs4.BeautifulSoup(r.text).find_all(attrs={'class': 'd-inline-block mb-1'}):
                    repository = item.find_all('a')[0].attrs['href']
                    self._repository_list.append(repository)
                    self._logger.info('Append repository: %s' % repository)
                _ = [item.attrs['href'] for item in bs4.BeautifulSoup(r.text).find_all(attrs={'class': 'paginate-container'})[0].find_all('a') if item.next == 'Next']
                if len(_) < 1:
                    break
                star_url = _[0]
            except Exception:
                self._logger.exception('Collect repository list exception')
        self._logger.info('Repository count: %d' % len(self._repository_list))

    def Login(self, gitea_username: str, gitea_password: str, gitea_proxy: str = None) -> bool:
        self._s_gitea.proxies = {'http': gitea_proxy, 'https': gitea_proxy} if gitea_proxy else {}
        self._logger.info('Gitea proxy: %s' % gitea_proxy)
        try:
            r = self._s_gitea.get(self._gitea_url)
            csrf = bs4.BeautifulSoup(r.text).find_all(attrs={'name': '_csrf'})[0].attrs['content']
            form_data = {'_csrf': csrf, 'user_name': gitea_username, 'password': gitea_password, 'remember': 'off'}
            r = self._s_gitea.post('%s/user/login' % self._gitea_url, data=form_data)
            if 'ui negative message flash-error' not in r.text:
                self._logger.info('Login gitea success')
                return True
            self._logger.info('Login error, tip: %s' % bs4.BeautifulSoup(r.text).find_all(attrs={'class', 'ui negative message flash-error'})[0].text)
        except Exception:
            self._logger.exception('Login to gitea exception')
        return False

    def Sync(self, gitea_organization: str, gitea_mirror: str, gitea_private: str, gitea_timeout: int = 300):
        for repository in self._repository_list:
            repository_name = repository.split('/')[2]
            repository_url = '%s/%s/' % (self._gitea_url, gitea_organization) + repository_name
            try:
                r = self._s_gitea.get(repository_url)
                if r.status_code != 404:
                    self._logger.info('Found repository(ignore): %s' % repository_url)
                    continue
            except Exception:
                self._logger.exception('Check repository found exception')
                continue
            repository_url = self._github_url + repository
            self._logger.info('Clone repository: %s' % repository_url)
            try:
                r = self._s_gitea.get('%s/repo/migrate' % self._gitea_url)
                csrf = bs4.BeautifulSoup(r.text).find_all(attrs={'name': '_csrf'})[0].attrs['content']
                form_data = {'_csrf': csrf, 'service': '2', 'clone_addr': repository_url, 'auth_token': '', 'mirror': gitea_mirror, 'lfs_endpoint': '', 'uid': '3', 'repo_name': repository_name, 'description': '', 'private': gitea_private}
                r = self._s_gitea.post('%s/repo/migrate' % self._gitea_url, data=form_data)
                csrf = bs4.BeautifulSoup(r.text).find_all(attrs={'name': '_csrf'})[0].attrs['content']
                task_number = bs4.BeautifulSoup(r.text).find_all(attrs={"id": "repo_migrating"})[0].attrs['task']
                start_time = int(time.time())
                while True:
                    if int(time.time()) - start_time > gitea_timeout:
                        self._logger.warning('Clone repository timeout, repository name: %s' % repository_name)
                        if r.json().get('repo-id'):
                            form_data = {'_csrf': csrf, 'id': r.json().get('repo-id')}
                            r = self._s_gitea.post(url='http://119.29.113.112:10017/admin/repos/delete',data=form_data)
                            if r.status_code == 200:
                                self._logger.info('Repository deleted')
                        break
                    time.sleep(3)
                    r = self._s_gitea.get('%s/user/task/%s?_csrf=%s' % (self._gitea_url, task_number, csrf))
                    if r.json().get('err'):
                        self._logger.warning('Clone repository error, repository name: %s' % repository_name)
                        break
                    if r.json().get('status') == 4:
                        self._logger.info('Clone repository success, repository name: %s' % repository_name)
                        break
                    self._logger.info('Clone %s repository(%d/%d)...' % (repository_name, int(time.time()) - start_time, int(gitea_timeout)))
            except Exception:
                self._logger.exception('Clone %s repository exception' % repository_name)
