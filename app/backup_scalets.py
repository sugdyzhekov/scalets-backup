#!/usr/bin/env python

from vscale import *

try:
    vscale_api = Vscale()
except VscaleError as e:
    print(e.message)
    exit(1)

for ctid in vscale_api.get_scalets_to_backup():
    server = VscaleScalet(ctid)
    print("Processing \"" + server.name + "\" (scalet id: " + str(server.id) + ")")

    print("Trying to backup server...")
    try:
        server.perform_backup()
        print("Backup task successfully started.")
    except VscaleApiError as e:
        if e.code == 409:
            print("Looks like we have today\'s backup. vscale.io says: \"{0}\"".format(e.message))
        else:
            print("Error during backup: \"" + e.message + "\"")
            exit(1)

    deleted_backups = []
    try:
        deleted_backups = server.rotate_backups()
    except VscaleApiError as e:
        print("Rotation of backups finished with error: \"{0}\", response code is {1}".format(e.message, str(e.code)))

    if deleted_backups:
        print("We had more backups than enough. The backups were rotated. Rotation result is:")
        for deleted_backup in deleted_backups:
            print("\tBackup \"{0}\" has been deleted.".format(deleted_backup.name))

    backup_list = server.backups()
    backup_list.sort(key=lambda x: x.created)
    print("Server has " + str(len(backup_list)) + " backups:")
    for backup in backup_list:
        print("\t\"{0}\" was created at {1}".format(backup.name, backup.created.strftime('%d.%m.%Y %H:%M')))

