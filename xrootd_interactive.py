import argparse
import logging

import questionary

from xrootd_utils import _check_file_or_directory  # , _check_redirector
from xrootd_utils import (stat, stat_dir, ls, interactive_ls,
                          copy_file_to_remote, copy_file_from_remote, del_file, del_dir, mv, mkdir,
                          dir_size, create_file_list)

parser = argparse.ArgumentParser(
    description='xrootd python bindings for dummies')
parser.add_argument('-r', '--redirector', help='root://xrd-redirector:1094/')
parser.add_argument('-u', '--user', help='username', required=True)
parser.add_argument('-b', '--basepath', help='default: /store/user/', default='/store/user/')
parser.add_argument('-l', '--loglevel', help='python loglevel={"WARNING", "INFO", "DEBUG"}', default='INFO')
args = vars(parser.parse_args())

##################################################
basepath: str
redirector: str
user: str
##################################################

# set logging
FORMAT = '%(message)s'
logging.basicConfig(format=FORMAT)
log = logging.getLogger()

if args["loglevel"] is not None:
    log.setLevel(args["loglevel"])

# set user
user = args["user"]
###################################################

############################################
# first, select a redirector and base path #
############################################
if args["redirector"] is not None:
    # set and check redirector
    redirector = args["redirector"]
    # _check_redirector(redirector)  # not supported from dcache door
else:
    answers0 = questionary.form(
        _redirector=questionary.select('Please select a redirector:',
                                       choices=[
                                           'root://cmsxrootd-kit.gridka.de:1094/, (RW) [default]',
                                           'root://cmsxrootd-redirectors.gridka.de:1094/, (RO) [not recommended]',
                                           'other'
                                       ])
    ).ask()
    if answers0["_redirector"] == 'other':
        redirector = str(input('Which redirector you want to use?'))
        if len(redirector) == 0:
            exit('No redirector specified! Please try again.')
    else:
        redirector = answers0["_redirector"].split(',')[0]  # take redirector from choices

log.info(f'Redirector selected: {redirector}')

# set and check base path
basepath = args["basepath"]
log.info(f'Selected base path: {basepath}')
if len(basepath) > 0 and (basepath[0] != '/' or basepath[-1] != '/'):
    exit('The base path has to begin and end with a "/"!')

log.info(f'Current base path: {basepath}')
log.debug(f'All inputs: {user}, {basepath}, {redirector}, {args["loglevel"]}')
#####################
# Start questionary #
#####################
while True:
    answers = questionary.form(
        _function=questionary.select('What do you want to do?',
                                     choices=[
                                         'exit',
                                         'ls',
                                         'interactive ls',
                                         'stat',
                                         'stat directory',
                                         'dir size',
                                         'rm file',
                                         'interactive file rm',
                                         'rm dir',
                                         'mv',
                                         'mkdir',
                                         'copy file to',
                                         'copy file from',
                                         'create file list',
                                         'change base path',
                                         'change redirector',
                                         'help',
                                     ])
    ).ask()

    ########## exit ##########
    if answers["_function"] == 'exit':
        exit(0)

    ########## ls ##########
    if answers["_function"] == 'ls':
        answers1 = questionary.form(
            _directory=questionary.text(f'Which directory? \n>{basepath}')
        ).ask()
        ls(redirector, basepath + answers1["_directory"])

    ########## interactive ls ##########
    if answers["_function"] == 'interactive ls':
        answers1 = questionary.form(
            _directory=questionary.text(f'Which directory? \n>{basepath}')
        ).ask()
        dirs, files = interactive_ls(redirector, basepath + answers1["_directory"])
        current_dir = basepath + answers1["_directory"]
        choices = ['exit'] + ['..'] + ['------Directories:------'] + dirs + [
            '------Files (will be stated):------'] + files
        stop = False
        while not stop:
            answers2 = questionary.form(
                _directory=questionary.select('Whats next?', choices=choices),
            ).ask()
            log.info(f'{answers2["_directory"]}')
            if '------' in answers2["_directory"]:
                continue
            if answers2["_directory"] == 'exit':
                break
            if answers2["_directory"] != '..':
                current_dir = answers2["_directory"]
            if answers2["_directory"] == '..':
                dirs, files = interactive_ls(redirector, '/'.join(current_dir.split('/')[:-2]))
                choices = ['exit'] + ['..'] + ['------Directories:------'] + dirs + [
                    '------Files (will be stated):------'] + files
                current_dir = '/'.join(current_dir.split('/')[:-2])
                continue
            if _check_file_or_directory(redirector, answers2["_directory"]) == 'dir':
                dirs, files = interactive_ls(redirector, answers2["_directory"])
                choices = ['exit'] + ['..'] + ['------Directories:------'] + dirs + [
                    '------Files (will be stated):------'] + files
            else:
                stat(redirector, answers2["_directory"])

    ########## stat ##########
    if answers["_function"] == 'stat':
        answers1 = questionary.form(
            _directory=questionary.text(f'Which file or directory do you want to stat? \
            \n  Note: To stat the directories content, please use "stat dir". \n >{basepath}')
        ).ask()
        stat(redirector, basepath + answers1["_directory"])

    ########## stat directory ##########
    if answers["_function"] == 'stat directory':
        answers1 = questionary.form(
            _directory=questionary.text(f'Which directory do you want to stat? \n >{basepath}')
        ).ask()
        stat_dir(redirector, basepath + answers1["_directory"], True, False)

    ########## rm file ##########
    if answers["_function"] == 'rm file':
        answers1 = questionary.form(
            _filepath=questionary.text(f'Which file do you want to delete? \n >{basepath}')
        ).ask()
        del_file(redirector, basepath + answers1["_filepath"], user, ask=True)

    ########## interactive file rm ##########
    if answers["_function"] == 'interactive file rm':
        answers1 = questionary.form(
            _directory=questionary.text(f'In which directory you want to delete a file? \n>{basepath}')
        ).ask()
        dirs, files = interactive_ls(redirector, basepath + answers1["_directory"])
        current_dir = basepath + answers1["_directory"]
        choices = ['exit'] + ['..'] + ['------Directories:------'] + dirs + [
            '------Files (will be DELETED!!):------'] + files
        stop = False
        while not stop:
            answers2 = questionary.form(
                _directory=questionary.select('Which file should be DELETED next?', choices=choices),
            ).ask()
            log.info(f'{answers2["_directory"]}')
            if '------' in answers2["_directory"]:
                continue
            if answers2["_directory"] == 'exit':
                break
            if answers2["_directory"] != '..':
                current_dir = answers2["_directory"]
            if answers2["_directory"] == '..':
                dirs, files = interactive_ls(redirector, '/'.join(current_dir.split('/')[:-2]))
                choices = ['exit'] + ['..'] + ['------Directories:------'] + dirs + [
                    '------Files (will be DELETED!!):------'] + files
                current_dir = '/'.join(current_dir.split('/')[:-2])
                continue
            if _check_file_or_directory(redirector, answers2["_directory"]) == 'dir':
                dirs, files = interactive_ls(redirector, answers2["_directory"])
                choices = ['exit'] + ['..'] + ['------Directories:------'] + dirs + [
                    '------Files (will be DELETED!!):------'] + files
            else:
                # Note: answers2["_directory"] is the file in this case!
                del_file(redirector, answers2["_directory"], user, True)
                choices.remove(answers2["_directory"])

    ########## rm dir ##########
    if answers["_function"] == 'rm dir':
        answers1 = questionary.form(
            _filepath=questionary.text(f'Which directory do you want to delete? \n >{basepath}')
        ).ask()
        del_dir(redirector, basepath + answers1["_filepath"], user, ask=True)

    ########## mv ##########
    if answers["_function"] == "mv":
        answers1 = questionary.form(
            _source=questionary.text(f'Which file do you want to move? \
                \n  Note: no relative paths! No overwrite! Destination has to be given explicit. \nSource: >{basepath}'
                                     ),
            _dest=questionary.text(f'\nDestination: >{basepath}'),
        ).ask()
        log.info(f'{answers1["_source"]} will be moved/renamed to {answers1["_dest"]}')
        mv(redirector, basepath + answers1["_source"], basepath + answers1["_dest"])

    ########## mkdir ##########
    if answers["_function"] == 'mkdir':
        answers1 = questionary.form(
            _filepath=questionary.text(
                f'Which directory do you want to create? (Full tree will be created!) \n >{basepath}'
            )
        ).ask()
        mkdir(redirector, basepath + answers1["_filepath"])

    ########## copy file to ##########
    if answers["_function"] == "copy file to":
        answers1 = questionary.form(
            _source=questionary.text(
                f'Which file do you want to copy to remote? Note: Complete path necessary! \nSource: >'
            ),
            _dest=questionary.text(f'Destination? Note: the path has to end with the desired filename! (/store/user/xyz/file.name) \
                    \n>{basepath}'
                                   )
        ).ask()
        log.info(f'{answers1["_source"]} will be copied to {basepath}{answers1["_dest"]}')
        copy_file_to_remote(redirector, answers1["_source"], basepath + answers1["_dest"])

    ########## copy file from ##########
    if answers["_function"] == "copy file from":
        answers1 = questionary.form(
            _source=questionary.text(f'Which file do you want to copy from remote? \
                     \nSource: >{basepath}'
                                     ),
            _dest=questionary.text(
                f'Destination? Note: the path has to end with the desired filename! (/home/user/dir/<filename.txt>) \n>'
            )
        ).ask()
        log.info(f'{answers1["_source"]} will be copied to {basepath}{answers1["_dest"]}')
        copy_file_from_remote(redirector, basepath + answers1["_source"], answers1["_dest"])

    ########## dir size ##########
    if answers["_function"] == 'dir size':
        answers1 = questionary.form(
            _filepath=questionary.text(f'Which directory? \n >{basepath}'
                                       )
        ).ask()
        dir_size(redirector, basepath + answers1["_filepath"], True)

    ########## create file list ##########
    if answers["_function"] == 'create file list':
        answers1 = questionary.form(
            _filepath=questionary.text(f'Which directory? \n >{basepath}'
                                       )
        ).ask()
        answers2 = questionary.form(
            exclude=questionary.text(f'Do you want to exclude fils (e.g. ".log") [Enter to continue]? \n >')
        ).ask()
        create_file_list(redirector, basepath + answers1["_filepath"], answers2["exclude"])

    ########## change base path ##########
    if answers["_function"] == 'change base path':
        basepath = str(input('Which basepath you want to use (default: /store/user/)?'))
        log.info(f'Selected base path: {basepath}')
        if basepath[0] != '/' or basepath[-1] != '/':
            exit('The base path has to begin and end with a "/"!')
        log.debug(f'[DEBUG] {redirector}, {basepath}')
        stat_dir(redirector, basepath, False, False)  # check, if dir exists
        log.info(f'Base path set to {basepath}')

    ########## change redirector ##########
    if answers["_function"] == 'change redirector':
        log.info(f'current redirector: {redirector}')
        answers1 = questionary.form(
            _redirector=questionary.select('Which redirector you want to use?',
                                           choices=[
                                               'root://cmsxrootd-redirectors.gridka.de:1094/, (RO)',
                                               'root://cmsxrootd-kit.gridka.de:1094/, (RW)',
                                               'other'
                                           ])
        ).ask()
        if answers1["_redirector"] == 'other':
            redirector = str(input('Which redirector you want to use?'))
            if len(redirector) == 0:
                exit('No redirector specified!')
        else:
            redirector = answers1["_redirector"].split(',')[0]
        log.info(f'Redirector changed to {redirector}')

    ########## help  ##########
    if answers["_function"] == 'help':
        help_dict = {
            '<exit>': 'exit the script',
            '<help>': 'print this help',
            '<ls>': 'static ls on a fixed directory',
            '<interactive ls>': 'interactive ls through the energy FTW!',
            '<stat>': 'xrdfs stat on file or directory',
            '<stat directory>': 'xrdfs stat on directory content',
            '<dir size>': 'prints the size of the directory. With DEBUG: gives sizes of sub-dirs',
            '<rm file>': 'remove a file from remote',
            '<interactive file rm>': 'select a file on CLI to remove',
            '<rm dir>': 'remove a directory on remote',
            '<mv>': 'move or rename a file/directory; paths need to be explicit!',
            '<mkdir>': 'xrdfs mkdir; full tree creation enabled',
            '<copy file to>': 'copy a file to remote',
            '<copy file from>': 'copy a file from remote',
            '<change base path>': 'changing the base path for convenience',
            '<change redirector>': 'change the redirector',
            '<create file list>': 'write out file list of given directory'
        }
        print('#####################################')
        print('# General notes and recommendations #')
        print('#####################################')
        print('First of all: ---BE CAREFUL!---')
        print('   Like xrdfs rm/gfal-rm, there is no real user access management! \
                \n   You can potentially delete everything...'
              )

        print('###################################################')
        print('-----------------------------------------------')
        for key, val in help_dict.items():
            print(key, ': ', val)
            print('-----------------------------------------------')
        print('###################################################')
