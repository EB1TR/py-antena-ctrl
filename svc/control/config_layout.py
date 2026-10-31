"""Split the legacy JSON layout without changing the public controller model."""

from copy import deepcopy
import json
from pathlib import Path


def split_legacy(stations, stacks, sixpack):
    installation = {'schema_version': 1, 'stations': {}, 'stacks': deepcopy(stacks), 'sixpack': deepcopy(sixpack)}
    initial = {'schema_version': 1, 'stations': {}, 'stacks': {}}
    for station, fields in stations.items():
        installation['stations'][station] = {key: value for key, value in fields.items()
                                              if key not in ('auto', 'band', 'rig', 'segmento')}
        initial['stations'][station] = {key: fields[key] for key in ('auto', 'band', 'rig')}
    for band, stack in installation['stacks'].items():
        initial['stacks'][band] = {'balun': stack.pop('balun'), 'outputs': {}}
        for index in ('1', '2', '3'):
            initial['stacks'][band]['outputs'][index] = stack[index].pop('estado')
    return installation, initial


def compose(installation, initial):
    if installation.get('schema_version') != 1 or initial.get('schema_version') != 1:
        raise RuntimeError('Versión de configuración no compatible')
    try:
        stacks = deepcopy(installation['stacks'])
        stations = {}
        for name in ('stn1', 'stn2'):
            state = initial['stations'][name]
            if type(state['auto']) is not bool or type(state['band']) is not int or type(state['rig']) is not int or state['rig'] not in (0, 1):
                raise ValueError('Estado inicial de estación inválido')
            if str(state['band']) not in installation['sixpack'][name[-1]]:
                raise ValueError('Banda inicial no configurada')
            stations[name] = dict(installation['stations'][name], **{key: state[key] for key in ('auto', 'band', 'rig')})
        for band, stack in stacks.items():
            state = initial['stacks'][band]
            if type(state['balun']) is not bool:
                raise ValueError('Balun inicial inválido')
            stack['balun'] = state['balun']
            for index in ('1', '2', '3'):
                if type(state['outputs'][index]) is not bool:
                    raise ValueError('Selección inicial de antena inválida')
                stack[index]['estado'] = state['outputs'][index]
        return stations, stacks, deepcopy(installation['sixpack'])
    except (KeyError, TypeError, ValueError) as error:
        raise RuntimeError(f'Configuración permanente/estado inicial inválidos: {error}') from error


def migrate(config_dir):
    """Create the new layout; never overwrite or remove existing configuration."""
    folder = Path(config_dir)
    load = lambda name: json.loads((folder / name).read_text(encoding='utf-8'))
    installation, initial = split_legacy({name: load(name + '.json') for name in ('stn1', 'stn2')},
                                       load('stacks.json'), load('sixpack.json'))
    compose(installation, initial)
    targets = [(folder / 'control/installation.json', installation), (folder / 'control/initial-state.json', initial)]
    if any(path.exists() for path, _ in targets):
        raise RuntimeError('El nuevo formato ya existe; no se sobrescribe. Revisa cfg/control/.')
    for path, data in targets:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open('x', encoding='utf-8') as file:
            json.dump(data, file, ensure_ascii=False, indent=2)
            file.write('\n')
    return [str(path) for path, _ in targets]


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Separa configuración permanente y estado inicial, conservando los ficheros anteriores.')
    parser.add_argument('config_dir', type=Path)
    print('\n'.join(migrate(parser.parse_args().config_dir)))
