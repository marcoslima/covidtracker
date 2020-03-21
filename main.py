import matplotlib.pyplot as plt

import requests
from datetime import datetime

from marshmallow import post_load, fields
import marshmallow


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
        response = requests.get(data_url)
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
        data = fields.List(fields.Dict)

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


def main():
    map_data = MapData.load(Settings.CACHE_FILE)
    pop = {'IT': 60.0, 'BR': 209.0, 'ES': 46.0, 'GB': 83.0, 'FR': 67.0}
    plot_data = []
    for x in map_data.data:
        a_data = x['date'].rstrip('\r')
        dia = datetime.strptime(a_data, '%m/%d/%y')
        data_row = {'dia': dia}
        for pais in [x for x in x['data'] if x['countrycode'] in
                                             ['BR', 'GB', 'FR', 'ES', 'IT']]:
            cc = pais['countrycode']
            cases = pais['totalcases']
            cases = float(cases) if cases else 0
            populacao = pop[cc]
            data_row = PlotData(dia,
                                cc,
                                pais['countrylabel'],
                                cases/pop[pais['countrycode']])
            plot_data.append(data_row)

    paises = set([x.sigla for x in plot_data])
    for pais in paises:
        corte = [x for x in plot_data if x.sigla == pais and x.casos > 0]
        data_x = [(x.dia - corte[0].dia).days for x in corte if x.sigla == pais]
        data_y = [x.casos for x in corte if x.sigla == pais]
        plt.plot(data_x, data_y, label=corte[0].pais)

    plt.title('Coronavirus | Brasil vs. Europa \n Escala logarítmica (t inicial = 1º caso registrado)')
    plt.xlabel('Tempo em dias')
    plt.ylabel('Casos / população')
    plt.yscale('log')
    plt.legend()
    plt.show()

if __name__ == '__main__':
    main()
