"""Create a Windows desktop shortcut to launch Monica AI."""
import os
import sys

def create_shortcut():
    desktop = os.path.join(os.environ['USERPROFILE'], 'Desktop')
    project = os.path.dirname(os.path.abspath(__file__))
    python_exe = sys.executable

    # Create .bat launcher
    bat_path = os.path.join(project, 'Launch_Monica.bat')
    with open(bat_path, 'w') as f:
        f.write('@echo off\n')
        f.write('title Monica AI\n')
        f.write(f'cd /d "{project}"\n')
        f.write(f'"{python_exe}" main.py\n')
        f.write('pause\n')
    print(f'Created launcher: {bat_path}')

    # Create shortcut via VBScript
    vbs_path = os.path.join(os.environ['TEMP'], 'create_monica_shortcut.vbs')
    shortcut_path = os.path.join(desktop, 'Monica AI.lnk')
    with open(vbs_path, 'w') as f:
        f.write('Set oWS = WScript.CreateObject("WScript.Shell")\n')
        f.write(f'Set oLink = oWS.CreateShortcut("{shortcut_path}")\n')
        f.write(f'oLink.TargetPath = "{bat_path}"\n')
        f.write(f'oLink.WorkingDirectory = "{project}"\n')
        f.write('oLink.Description = "Launch Monica AI Assistant"\n')
        f.write('oLink.WindowStyle = 1\n')
        f.write('oLink.Save\n')

    os.system(f'cscript //nologo "{vbs_path}"')
    os.remove(vbs_path)

    if os.path.exists(shortcut_path):
        print(f'Desktop shortcut created: {shortcut_path}')
    else:
        print('Shortcut creation failed - creating .bat on desktop instead')
        import shutil
        shutil.copy(bat_path, os.path.join(desktop, 'Launch Monica AI.bat'))
        print(f'Created: {os.path.join(desktop, "Launch Monica AI.bat")}')

if __name__ == '__main__':
    create_shortcut()
