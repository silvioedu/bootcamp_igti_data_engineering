import prefect
from prefect import task, Flow


@task
def hello_world():
    logger = prefect.context.get("logger")
    logger.info("Hello Workd do Prefect Cloud!")


with Flow("Hello World") as flow:
    hello_world()

flow.register(project_name='Hello World')

# prefect auth create-token -n my-runner-token -s RUNNER
flow.run_agent(token='dE5zGVFdfzZpNj6bTBcweg')
