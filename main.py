import matplotlib.pyplot as plt

import requests
from datetime import datetime

from marshmallow import post_load, fields
import marshmallow
from enum import Enum


class Settings:
    CACHE_FILE = 'cache.dat'
    CACHE_TIME_IN_HOURS = 8
    MAPDATA_URL = 'https://thevirustracker.com/timeline/map-data.json'


class MapData:
    def __init__(self, access_time=None, data=None):
        self.access_time = access_time
        self.data = data

    def request_data(self):
        print('Requesting updated data from API')
        data_url = Settings.MAPDATA_URL
        headers = {'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
                   'accept-encoding': 'gzip, deflate, b',
                   'accept-language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
                   'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.88 Safari/537.36'
                }

        try:
            response = requests.get(data_url, headers=headers)
            # print(f'Request result: {response.status_code}')
            # print(f'Request response: {response.content}')
        except Exception as e:
            print(f'Erro fazendo request: {type(e)}: {e}')
            print(f'Response: {response.content}')

        self.access_time = datetime.now()
        self.data = response.json()

        self.save(Settings.CACHE_FILE)

    def save(self, filename):
        str_data = self.Schema().dumps(self)
        with open(filename, 'w') as f:
            f.write(str_data)

    @classmethod
    def load(cls, filename):
        try:
            with open(filename, 'r') as f:
                str_data = f.read()
            instancia = cls.Schema().loads(str_data)
        except FileNotFoundError:
            instancia = cls()
            instancia.request_data()
            return instancia

        if instancia.is_request_needed:
            instancia.request_data()
        else:
            print(f'Using cached data from {instancia.access_time}')

        return instancia

    @property
    def is_request_needed(self):
        tempo = datetime.now() - self.access_time
        return (tempo.seconds / 3600) > Settings.CACHE_TIME_IN_HOURS

    class Schema(marshmallow.Schema):
        access_time = fields.DateTime(format='iso')
        data = fields.Dict()

        @post_load
        def on_load(self, data, many, partial):
            return MapData(**data)


class PlotData:
    def __init__(self, dia, sigla, pais, casos):
        self.dia = dia
        self.sigla = sigla
        self.pais = pais
        self.casos = float(casos) if casos else 0
        

    def __repr__(self):
        return f'{self.dia}: {self.sigla} - {self.casos}'

def _get_y_value(row, show_cases=True):
    if show_cases:
        return row['cases']
    else:
        return row['deaths']


def main():
    class DataToShow(Enum):
        Deaths = 0
        Cases = 1

    cases_or_deaths = DataToShow.Deaths
    relativo_populacao = True
    log_scale = True

    mc = input('Mortes ou Casos? (M/c)').upper()
    if mc and mc == 'C':
        cases_or_deaths = DataToShow.Cases
    res = input('Relativo à população? (S/n)').upper()
    if res and res == 'N':
        relativo_populacao = False
    res = input('Escala logarítmica? (S/n)').upper()
    if res and res == 'N':
        log_scale = False


    map_data = MapData.load(Settings.CACHE_FILE)
    pop = {'IT': 60.0, 'BR': 209.0, 'ES': 46.0, 'GB': 83.0, 'FR': 67.0}
    plot_data = []
    for x in map_data.data['data']:
        # import ipdb; ipdb.set_trace()
        a_data = x['date'].rstrip('\r')
        dia = datetime.strptime(a_data, '%m/%d/%y')
        data_row = {'dia': dia}
        if x['countrycode'] in ['BR', 'GB', 'FR', 'ES', 'IT']:
            cc = x['countrycode']
            populacao = pop[cc]
            cases = _get_y_value(x, show_cases=cases_or_deaths==DataToShow.Cases)
            cases = float(cases) if cases else 0
            if relativo_populacao:
                cases /= populacao

            data_row = PlotData(dia,
                                cc,
                                x['countrycode'],
                                cases)
            plot_data.append(data_row)


    paises = set([x.sigla for x in plot_data])
    for pais in paises:
        corte = sorted([x for x in plot_data if x.sigla == pais and x.casos > 0], key=lambda x: x.dia)
        data_x = [(x.dia - corte[0].dia).days for x in corte if x.sigla == pais]
        data_y = [x.casos for x in corte if x.sigla == pais]
        plt.plot(data_x, data_y, label=corte[0].pais)

    title_logaritmico = 'Escala logarítmica ' if log_scale else ''
    plt.title(f'Coronavirus | Brasil vs. Europa \n {title_logaritmico}(t inicial = 1º caso registrado)')
    plt.xlabel('Tempo em dias')
    y_label = 'Mortes' if cases_or_deaths == DataToShow.Deaths else 'Casos'
    if relativo_populacao:
        y_label += f' / milhão de habitantes'

    plt.ylabel(y_label)
    if log_scale:
        plt.yscale('log')
    plt.grid(which='both', axis='both')
    plt.legend()
    plt.show()

if __name__ == '__main__':
    main()
