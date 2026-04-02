import boto3
import os


dynamodb_url = os.environ.get('DYNAMODB_URL')
aws_region = os.environ.get('AWS_REGION')
polls_table_name = os.environ.get('DYNAMODB_TABLE_POLLS', 'polls')

db_client = boto3.resource('dynamodb', region_name=aws_region)
if dynamodb_url:
    db_client = boto3.resource('dynamodb', endpoint_url=dynamodb_url, region_name=aws_region)
polls_table = db_client.Table(polls_table_name)

def save_poll(poll: dict) -> bool:
  """
  Save poll to dynamodb
  :param poll:
  :return:
  """
  try:
    polls_table.put_item(Item=poll)
    return True
  except Exception as e:
    print(f"Error saving poll: {e}")
    return False