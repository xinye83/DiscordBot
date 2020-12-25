import asyncio
import os
import datetime

# get character name from **simc addon** output
def get_name_from_profile(string):
    i = string.find(' ', 2, 32)
    return string[2:i]

# get simc version info from **simc** output
def get_simc_version(string):
    return '_' + string.partition('\n')[0] + '_'

# get character class & spec from **simc** output
def get_class_spec(string):
    i = string.find('Player:', 0, len(string)) + len('Player:') + 1
    i = string.find(' ', i, len(string)) + 1
    i = string.find(' ', i, len(string)) + 1
    j = string.find(' ', i, len(string))
    _class = string[i:j]

    if _class == 'demonhunter':
        _class = 'demon hunter'

    _class = _class.title()

    i = j + 1
    j = string.find(' ', i, len(string))
    spec = string[i:j]

    if spec == 'beast_mastery':
        spec = 'beast mastery'

    spec = spec.title()

    return _class, spec

# get simulation dps from **simc** output
def get_dps(string):
    i = string.find('DPS=', 0, len(string)) + 4
    j = string.find('.', i, len(string)) + 3
    dps = string[i:j]
    return dps

# get stat scaling factors from **simc** output
def get_scale(string, name):
    i = string.find('Scale Factors:\n  ' + name, 0, len(string))
    i += len('Scale Factors:\n  ' + name)
    j = string.find('\n', i, len(string))

    factors = string[i:j].strip().split('  ')

    width1 = 0
    width2 = 0

    table = []
    for factor in factors:
        i = factor.find('=', 0, len(factor))
        j = factor.find('(', i, len(factor))

        width1 = max(width1, i)
        width2 = max(width2, j - i - 1)

        table.append([factor[0: i], factor[i + 1: j]])

    width1 = max(width1, len('Stat'))
    width2 = max(width2, len('Scale'))

    temp = '+-' + '-' * width1 + '-+-' + '-' * width2 + '-+\n'

    scale = '```\n' + temp
    scale += '| Stat' + ' ' * (width1 - len('Stat')) + ' | Scale' + ' ' * (width2 - len('Scale')) + ' |\n'
    scale += temp
    for factor, score in table:
        scale += '| ' + factor + ' ' * (width1 - len(factor)) + ' | ' + score + ' ' * (width2 - len(score)) + ' |\n'

    scale += temp
    scale += '```'

    return scale

async def SimulationCraft(name=None, profile=None, stat=False):
    if name is None and profile is None:
        return -1

    if name is not None and profile is not None:
        return -1

    simc = '/home/xye/simc/engine/simc'
    threads = 1

    if name is None:
        name = get_name_from_profile(profile)

    name = name.title()

    output_file = name + '.html'

    if os.path.exists(output_file):
        os.remove(output_file)

    cmd = simc
    cmd += ' html=' + output_file
    cmd += ' threads=' + str(threads)
    cmd += ' calculate_scale_factors='
    if stat:
        cmd += '1'
    else:
        cmd += '0'

    if profile is None:
        cmd += ' armory=us,illidan,' + name.lower()
    else:
        # store profile string in a temp file
        input_file = datetime.datetime.now().isoformat() + '.in'
        fp = open(input_file, 'w')
        fp.write(profile)
        fp.close()
        
        cmd += ' ' + input_file

    p = await asyncio.create_subprocess_shell(
        cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE)

    await p.wait()

    stdout, stderr = await p.communicate()

    stdout = stdout.decode("utf-8")
    stderr = stderr.decode("utf-8")

    if p.returncode:
        print('\n****** simc returned error code ' + str(p.returncode))
        print('****** stdout\n' + stdout)
        print('****** stderr\n' + stderr)
        return p.returncode

    version = get_simc_version(stdout)
    _class, spec = get_class_spec(stdout)
    dps = get_dps(stdout)
    if stat:
        scale = get_scale(stdout, name)
    else:
        scale = ''

    if profile is not None:
        os.remove(input_file)

    return p.returncode, version, output_file, name, _class, spec, dps, scale
