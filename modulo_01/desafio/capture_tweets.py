import json
from tweepy import OAuthHandler, Stream, StreamListener
from datetime import datetime, timedelta
import pandas as pd
import sqlite3
import prefect
from prefect import task, Flow
from prefect.schedules import IntervalSchedule


schedule = IntervalSchedule(interval=timedelta(minutes=10))


class MyListener(StreamListener):

    def __init__(self, limit, file):
        self.count = 0
        self.limit = limit
        self.out = file

    def on_data(self, data):
        item_string = json.dumps(data)
        self.out.write(item_string + '\n')

        if self.count >= self.limit:
            return False

        self.count += 1
        return True

    def on_error(self, status):
        print(status)


def tweet_para_df(tweet):
    try:
        df_tratado = pd.DataFrame(tweet).reset_index(drop=True).iloc[:1]
        df_tratado.drop(columns=['quote_count', 'reply_count', 'retweet_count',
                                 'favorite_count', 'favorited', 'retweeted',
                                 'user', 'entities', 'retweeted_status',
                                 'quoted_status_id', 'quoted_status_id_str',
                                 'quoted_status', 'quoted_status_permalink'],
                        inplace=True)

        df_tratado['user_id'] = tweet['user']['id']
        df_tratado['user_id_str'] = tweet['user']['id_str']
        df_tratado['user_screen_name'] = tweet['user']['screen_name']
        df_tratado['user_location'] = tweet['user']['location']
        df_tratado['user_description'] = tweet['user']['description']
        df_tratado['user_protected'] = tweet['user']['protected']
        df_tratado['user_verified'] = tweet['user']['verified']
        df_tratado['user_followers_count'] = tweet['user']['followers_count']
        df_tratado['user_friends_count'] = tweet['user']['friends_count']
        df_tratado['user_created_at'] = tweet['user']['created_at']

        user_mentions = []

        for i in range(len(tweet['entities']['user_mentions'])):
            dicionario_base = tweet['entities']['user_mentions'][i].copy()
            dicionario_base.pop('indices', None)
            df = pd.DataFrame(dicionario_base, index=[0])
            df = df.rename(columns={
                'screen_name': 'entities_screen_name',
                'name': 'entities_name',
                'id': 'entities_id',
                'id_str': 'entities_id_str'
            })
            user_mentions.append(df)

        dfs = []
        for i in user_mentions:
            dfs.append(
                pd.concat([df_tratado.copy(), i], axis=1)
            )
        df_final = pd.concat(dfs, ignore_index=True)
    except:
        return None

    return df_final


@task
def get_tweets():
    # Cadastrar chaves de acesso
    CONSUMER_KEY = 'col5CfxgzBR7HpCH5SOUugslb'
    CONSUMER_SECRET = 'm9awrJjzNrQVX1htLRmSdf4flJ2j0oPwuMQMdOBSU7Ordrlcdw'
    ACESS_TOKEN = '1326514645117571072-DisgVOkPywAY1S7GNV8HhoYTty4D2i'
    ACESS_TOKEN_SECRET = 'Y75DpuZB2t3iLbdOiJheFG4HEFt6jXJZuWa0CBGwB5ZH4'

    # Definir um arquivo de saída para armazenar os tweets coletados
    data_hoje = datetime.now().strftime('%Y-%m-%d-%H-%M-%S')
    output_file = f'collected_tweets_{data_hoje}.txt'
    print(f'Arquivo de saida gerado: {output_file}')
    out = open(output_file, 'w')

    # Definir palavras para rastrear
    track_words = ['Netflix', 'Crackle', 'PopcornFlix', 'Crunchyroll',
                   'Amazon Video', 'HBOGO', 'Globosat Play', 'Youtube',
                   'Twitch', 'Telecine Play', 'Disney Plus']
    limite = 100

    logger = prefect.context.get("logger")
    logger.info(f'Rastreando palavras {track_words}')

    # Iniciando o fluxo de captura
    ltn = MyListener(limite, out)
    auth = OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
    auth.set_access_token(ACESS_TOKEN, ACESS_TOKEN_SECRET)

    stream = Stream(auth, ltn)
    stream.filter(track=track_words)
    print('Dados capturados')
    logger.info(f'Arquivo gerado {output_file}')

    return output_file


@task
def ler_tweets(output_file):
    tweets_capturados = []
    with open(output_file, 'r') as file:
        tweets_capturados = file.readlines()
    return tweets_capturados


@task
def tratar_tweets_individualmente(tweets_capturados):
    return [json.loads(json.loads(t)) for t in tweets_capturados]


@task
def transformar_tweets_para_df(captured_tweets):
    return [tweet_para_df(tweet) for tweet in captured_tweets]


@task
def limpar_lista(parseados):
    return [i for i in parseados if i is not None]


@task
def transformar_em_df(parseados_limpos):
    return pd.concat(parseados_limpos, ignore_index=True)


@task
def inserir_banco_dados(df):
    conn = sqlite3.connect("./tweets_stream.db")
    df.to_sql('tweets', con=conn, if_exists='append')
    print("Dados inseridos no BD")
    conn.close()


with Flow('Titanic01', schedule=schedule) as flow:
    output_file = get_tweets()
    tweets_capturados = ler_tweets(output_file)
    captured_tweets = tratar_tweets_individualmente(tweets_capturados)
    parseados = transformar_tweets_para_df(captured_tweets)
    parseados_limpos = limpar_lista(parseados)
    df_tratado = transformar_em_df(parseados_limpos)
    banco = inserir_banco_dados(df_tratado)

# prefect create project IGTI --description "Projetos do bootcamp de engenharia de dados do IGTI"
flow.register(project_name='IGTI')

# prefect auth create-token -n my-runner-token -s RUNNER
flow.run_agent(token='dE5zGVFdfzZpNj6bTBcweg')
