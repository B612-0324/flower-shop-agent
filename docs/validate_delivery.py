"""在隔离验证环境中执行，记录真实命令、返回码和完整日志。"""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'outputs'
OUT.mkdir(exist_ok=True)
LOG = OUT / 'logs'
LOG.mkdir(exist_ok=True)
commands = []


def run(name, args, cwd=ROOT, env=None):
    result = subprocess.run([str(a) for a in args], cwd=cwd, env=env,
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                            encoding='utf-8', errors='replace')
    (LOG / (name+'.log')).write_text(result.stdout, encoding='utf-8')
    commands.append(dict(name=name, command=[str(a) for a in args],
                         returncode=result.returncode))
    print(name, result.returncode)
    if result.returncode:
        raise RuntimeError(result.stdout)
    return result


env = dict(os.environ, PYTHONUTF8='1', PYTHONIOENCODING='utf-8')
run('pytest', [sys.executable, '-m', 'pytest', ROOT/'tests', '-v',
               '--junitxml='+str(OUT/'test-results.xml')], env=env)
run('unittest', [sys.executable, '-m', 'unittest', 'discover', '-s', ROOT/'tests',
                 '-p', 'test_regression.py', '-v'], env=env)
for days, seed in [(7,42),(14,7)]:
    run(f'simulation_{days}d_seed{seed}', [sys.executable, ROOT/'main.py', '--days',days,
        '--seed',seed,'--output-dir',OUT/f'demo_{days}d_seed{seed}'], env=env)
run('wheel_build',[sys.executable,'-m','pip','wheel',ROOT,'--no-deps',
                   '--no-build-isolation','--wheel-dir',OUT/'dist'], env=env)
wheel = next((OUT/'dist').glob('*.whl'))
with tempfile.TemporaryDirectory() as directory:
    target = Path(directory)/'installed'
    run('wheel_install',[sys.executable,'-m','pip','install','--no-deps',
                         '--target',target,wheel],cwd=directory,env=env)
    installed_env = dict(env, PYTHONPATH=str(target))
    run('installed_module',[sys.executable,'-m','flower_shop.cli','--days','1',
                            '--output-dir',OUT/'installed_demo'],cwd=directory,env=installed_env)
    installed_python = Path(sys.executable).resolve()
    # pip --target产生的控制台脚本直接运行，借助PYTHONPATH加载隔离目标包。
    script = next(target.rglob('flower-shop.exe'))
    run('installed_console',[script,'--days','1','--no-dashboard',
                             '--output-dir',OUT/'console_demo'],cwd=directory,env=installed_env)
(OUT/'validation_commands.json').write_text(json.dumps(commands,ensure_ascii=False,indent=2),encoding='utf-8')
print('全部验证完成')
