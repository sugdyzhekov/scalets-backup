import requests
from datetime import date, datetime
import os


class VscaleError(Exception):
    def __init__(self, message):
        self.message = message

    def __str__(self):
        return self.message


class VscaleApiError(Exception):
    def __init__(self, response):
        self.code = response.status_code
        self.message = response.headers["Vscale-Error-Message"]
        self.response = response

    def __str__(self):
        return repr(self.response)


class VscaleAPI:
    def __init__(self):
        if 'vscale_token' not in globals():
            vscale_token = os.environ.get('VSCALE_TOKEN')
            if not vscale_token:
                raise VscaleError('Please provide vscale.io API token as global `vscale_token`'
                                  ' or env var `VSCALE_TOKEN`')

        self.api = "https://api.vscale.io/v1"
        # 7ec99d8f3a0271c4049b697df472ec6c17f850dedcbc098c9c7873ef00f50b53
        self.token = token = {'X-Token': vscale_token}  # global var

    def _prepare_call(self, func):
        def decorated():
            r = func()
            if r.status_code != 200:
                raise VscaleApiError(r)
            return r.json()
        return decorated


class Vscale(VscaleAPI):
    def __init__(self):
        VscaleAPI.__init__(self)
        self.scalets = self.get_scalets_list()

    def get_scalets_list(self):
        api_call = self._prepare_call(lambda: requests.get(self.api + '/scalets', headers=self.token))
        scalets = api_call()
        scalets_by_ctid = {}
        for scalet in scalets:
            scalets_by_ctid[scalet["ctid"]] = scalet

        return scalets_by_ctid

    def get_scalet(self, scalet_id):
        return self.scalets[scalet_id]

    def _scalets_to_backup(self):
        url = self.api + "/scalets/tags"
        response = requests.get(url, headers=self.token)

        return response

    def get_scalets_to_backup(self):
        api_call = self._prepare_call(self._scalets_to_backup)
        tags = api_call()
        for tag in tags:
            if tag["name"] == "to_backup":
                return tag["scalets"]

        return []


class VscaleScalet(Vscale):
    def __init__(self, scalet_id):
        Vscale.__init__(self)
        self.id = scalet_id
        scalet = self.get_scalet(scalet_id)
        self.name = scalet["name"]

    def _backups(self):
        url = self.api + "/backups"
        response = requests.get(url, headers=self.token)

        return response

    def backups(self):
        api_call = self._prepare_call(self._backups)
        snapshots = api_call()
        backup_list = []
        for snapshot in snapshots:
            # Backup should be already created, exists not locked by another process
            if snapshot["scalet"] == self.id and \
                            snapshot["is_deleted"] is not True and \
                            snapshot["status"] == "finished" and \
                            snapshot["locked"] is not True:
                item = VscaleScaletBackup(snapshot["id"])
                backup_list.append(item)

        return backup_list

    def _perform_backup(self):
        url = self.api + "/scalets/" + str(self.id) + "/backup"
        payload = {'name': self.name + " " + str(date.today())}
        response = requests.post(url, headers=self.token, json=payload)

        return response

    def perform_backup(self):
        api_call = self._prepare_call(self._perform_backup)
        api_call()

    def rotate_backups(self, retain=3):
        backup_list = self.backups()
        backup_list.sort(key=lambda x: x.created)
        backup_list.reverse()
        backups_amount = len(backup_list)

        list_of_deleted = []
        if backups_amount > retain:
            too_old = backup_list.pop()
            list_of_deleted.append(too_old)
            too_old.delete()
            list_of_deleted + self.rotate_backups(retain)

        return list_of_deleted


class VscaleScaletBackup(Vscale):
    def __init__(self, backup_id):
        Vscale.__init__(self)
        self.id = backup_id
        info = self.get_info()
        self.created = datetime.strptime(info["created"], '%d.%m.%Y %H:%M:%S')
        self.name = info["name"]

    def _get_info(self):
        url = self.api + '/backups/' + self.id
        response = requests.get(url, headers=self.token)

        return response

    def get_info(self):
        api_call = self._prepare_call(self._get_info)

        return api_call()

    def _delete(self):
        url = self.api + "/backups/" + str(self.id)
        response = requests.delete(url, headers=self.token)

        return response

    def delete(self):
        api_call = self._prepare_call(self._delete)
        api_call()
