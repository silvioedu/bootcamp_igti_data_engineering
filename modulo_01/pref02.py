from datetime import datetime, timedelta
import pendulum
import prefect
from prefect import task, Flow
from prefect.schedules import CronSchedule
import pandas as pd
from io import BytesIO
import zipfile
import requests

schedule = CronSchedule(
    cron="*/30 * * * *",
    start_date=pendulum.datetime(2021, 3, 12, 17, 00, tz='America/Sao_Paulo')
)


@task
def get_raw_data():
    url = 'http://download.inep.gov.br/microdados/microdados_enem_2019.zip'
    filebytes = BytesIO(
        requests.get(url).content
    )

    logger = prefect.context.get('logger')
    logger.info('Dados obtidos')

    # Extrair o conteudo do zipfile
    myzip = zipfile.ZipFile(filebytes)
    myzip.extractall()
    path = './DADOS/'
    return path


@task
def aplica_filtros(path):
    enade = pd.read_csv(path + 'MICRODADOS_ENEM_2019.csv',
                        sep=';', decimal=',', nrows=1000)

    logger = prefect.context.get('logger')
    logger.info(f'Colunas do df sao: {enade.columns}')

    enade = enade.loc[
        (enade.NU_IDADE > 20) &
        (enade.NU_IDADE < 40) &
        (enade.NT_GER > 0)
    ]
    return enade


@task
def constroi_idade_centralizada(df):
    idade = df[['NU_IDADE']]
    idade['idadecent'] = idade.NU_IDADE - idade.NU_IDADE.mean()
    return idade[['idadecent']]


@task
def constroi_idade_cent_quad(df):
    idadecent = df.copy()
    idadecent['idade2'] = idadecent.idadecent ** 2
    return idadecent[['idade2']]


@task
def constroi_est_civil(df):
    filtro = df[['QE_I01']]
    filtro['estcivil'] = filtro.QE_I01.replace({
        'A': 'Solteiro',
        'B': 'Casado',
        'C': 'Separado',
        'D': 'Viuvo',
        'E': 'Outro'
    })
    return filtro[['estcivil']]


@task
def constroi_cor(df):
    filtro = df[['QE_I02']]
    filtro['cor'] = filtro.QE_I02.replace({
        'A': 'Branca',
        'B': 'Preta',
        'C': 'Amarela',
        'D': 'Parda',
        'E': 'Indigena',
        'F': '',
        ' ': ''
    })
    return filtro[['cor']]


@task
def constroi_escopai(df):
    filtro = df[['QE_I_04']]
    filtro['escopai'] = filtro.QE_I04.replace({
        'A': 0,
        'B': 1,
        'C': 2,
        'D': 3,
        'E': 4,
        'F': 5
    })
    return filtro[['escopai']]


@task
def constroi_escomae(df):
    filtro = df[['QE_I_05']]
    filtro['escomae'] = filtro.QE_I05.replace({
        'A': 0,
        'B': 1,
        'C': 2,
        'D': 3,
        'E': 4,
        'F': 5
    })
    return filtro[['escomae']]


@task
def constroi_renda(df):
    filtro = df[['QE_I_08']]
    filtro['renda'] = filtro.QE_I08.replace({
        'A': 0,
        'B': 1,
        'C': 2,
        'D': 3,
        'E': 4,
        'F': 5,
        'G': 6
    })
    return filtro[['renda']]


@task
def join_data(df, idadecent, idadequadrado, estcivil, cor,
              escopai, escomae, renda):
    final = pd.concat([df, idadecent, idadequadrado, estcivil, cor,
                       escopai, escomae, renda],
                      axis=1)

    logger = prefect.context.get('logger')
    logger.info(final.head().to_json())
    final.to_csv('enade_tratato.csv', index=False)


with Flow('Enade', schedule) as flow:
    path = get_raw_data()
    filtro = aplica_filtros(path)
    idadecent = constroi_idade_centralizada(filtro)
    idadequadrado = constroi_idade_cent_quad(idadecent)
    estcivil = constroi_est_civil(filtro)
    cor = constroi_cor(filtro)
    escomae = constroi_escomae(filtro)
    escopai = constroi_escopai(filtro)
    renda = constroi_renda(filtro)

    j = join_data(filtro, idadecent, idadequadrado, estcivil, cor,
                  escomae, escopai, renda)

# prefect create project IGTI --description "Projetos do bootcamp de engenharia de dados do IGTI"
flow.register(project_name='IGTI', idempotency_key=flow.serialized_hash())

# prefect auth create-token -n my-runner-token -s RUNNER
flow.run_agent(token='dE5zGVFdfzZpNj6bTBcweg')
