import re

from .cache import memoized


@memoized
def get_physical_memory_size():
    meminfo_path = '/proc/meminfo'
    info_pattern = re.compile(r'(?P<key>[^:]+):\s+(?P<value>\d+).*')

    try:
        with open(meminfo_path) as f:
            for line in f:
                match = info_pattern.match(line)
                if match:
                    info = match.groupdict()
                    if info['key'] == 'MemTotal':
                        return int(info['value']) * 1024
    except Exception as e:
        raise Exception('Something went wrong!: {0}'.format(e))
