import jsonpickle as jp
from PyTib.common import open_file, write_file, pre_process, de_pre_process

jp.set_encoder_options('simplejson', sort_keys=True, indent=4, ensure_ascii=False)


def parse_monlam_verbs(raw_file):
    lines = raw_file.strip().split('\n')
    verbs = {}
    for line in lines:
        entry, info = line.split(' | ')
        meanings = info.split('+')
        for meaning in meanings:
            sections = meaning.split('_')
            characteristics = {'བྱ་ཚིག': False, 'དུས།': False, 'ཐ་དད་མི་དད།': False, 'འབྲི་ཚུལ་གཞན།': False}
            while sections != []:
                char = sections.pop()
                if char in ['འདས།', 'འདསཔ', 'འདས་པ།']:
                    characteristics['དུས།'] = 'འདས་པ།'
                elif char in ['ད་ལྟ་བ', 'དལྟབ', 'ད་ལྟ་བ།']:
                    characteristics['དུས།'] = 'ད་ལྟ་བ།'
                elif char in ['མ་འོངས་པ།', 'མའོངསཔ', 'མ་འོངས།', 'མ་འོངས་པ']:
                    characteristics['དུས།'] = 'མ་འོངས་པ།'
                elif char in ['སྐུ་ཚིག', 'སྐུལ་ཚིག', 'སྐུལཚིག', 'སྐུལ་ཚིག།']:
                    characteristics['དུས།'] = 'སྐུལ་ཚིག'
                elif char == 'ཐ་དད་པ':
                    characteristics['ཐ་དད་མི་དད།'] = 'ཐ་དད་པ།'
                elif char == 'ཐ་མི་དད་པ':
                    characteristics['ཐ་དད་མི་དད།'] = 'ཐ་མི་དད་པ།'
                elif char == 'གཟུགས་མི་འགྱུར་བ':
                    characteristics['དུས།'] = 'གཟུགས་མི་འགྱུར་བ།'
                elif char == 'འབྲི་ཚུལ':
                    characteristics['འབྲི་ཚུལ་གཞན།'] = True
                elif char not in ['བྱ་ཚིག', '###']:
                    characteristics['བྱ་ཚིག'] = char
            current_meaning = {}
            for char in characteristics:
                if characteristics[char]:
                    current_meaning[char] = characteristics[char]
            if entry not in verbs.keys():
                verbs[entry] = []
            if current_meaning and current_meaning not in verbs[entry]:
                verbs[entry].append(current_meaning)
    return verbs


def find_meaning_profiles(verbs):
    profiles = []
    for verb in verbs:
        for meaning in verbs[verb]:
            profile = [a for a in meaning]
            if profile not in profiles:
                profiles.append(profile)
    return profiles


#raw = open_file('./resources/monlam1_verbs.txt')
#parsed = parse_monlam_verbs(raw)
#write_file('monlam_verbs.json', jp.encode(parsed))

path = './resources/monlam_verbs.json'
verbs = jp.decode(open_file(path))
# write_file(path, jp.encode(verbs))  # to sort and overwrite the manually updated template
#print(find_meaning_profiles(verbs))
# [['བྱ་ཚིག', 'ཐ་དད་མི་དད།', 'དུས།'], ['བྱ་ཚིག', 'དུས།'], ['ཐ་དད་མི་དད།', 'དུས།'], ['ཐ་དད་མི་དད།'], ['བྱ་ཚིག', 'འབྲི་ཚུལ་གཞན།'], ['བྱ་ཚིག', 'འབྲི་ཚུལ་གཞན།', 'དུས།'], ['དུས།']]
for profile in [['བྱ་ཚིག', 'ཐ་དད་མི་དད།', 'དུས།'], ['བྱ་ཚིག', 'དུས།'], ['ཐ་དད་མི་དད།', 'དུས།'], ['ཐ་དད་མི་དད།'], ['བྱ་ཚིག', 'འབྲི་ཚུལ་གཞན།'], ['བྱ་ཚིག', 'འབྲི་ཚུལ་གཞན།', 'དུས།'], ['དུས།']]:
    occurences = []
    for verb in verbs:
        for meaning in verbs[verb]:
            if sorted([a for a in meaning]) == sorted(profile):
                if 'བྱ་ཚིག' in meaning.keys():
                    meaning['བྱ་ཚིག'] = ''
                if meaning not in occurences:
                    occurences.append(meaning)
    print(profile)
    print(occurences)
