import boto3
import os


dynamodb_url = os.environ.get('DYNAMODB_URL')
aws_region = os.environ.get('AWS_REGION')
polls_table_name = os.environ.get('DYNAMODB_TABLE_POLLS', 'polls')
votes_table_name = os.environ.get('DYNAMODB_TABLE_VOTES', 'votes')

db_client = boto3.resource('dynamodb', region_name=aws_region)
if dynamodb_url:
    db_client = boto3.resource('dynamodb', endpoint_url=dynamodb_url, region_name=aws_region)
polls_table = db_client.Table(polls_table_name)
votes_table = db_client.Table(votes_table_name)

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

def get_poll(poll_id: str) -> dict:
  """
  Get poll from dynamodb
  :param poll_id:
  :return: dict
  """
  try:
    poll_data=polls_table.get_item(Key={"poll_id": poll_id})
    return poll_data.get('Item')
  except Exception as e:
    print(f"Error retrieving poll: {e}")
    return None

def save_vote(poll_id: str, vote_info: str, vote_id: str, vote_time: str) -> bool:
  """
  :param poll_id: The poll id
  :param vote_info: The vote info passed from the vote function
  :param vote_id: The vote id
  :param vote_time: The vote time
  :return: Returns true if vote is saved successfully
  """
  try:
    votes_table.put_item(Item={
      "poll_id": poll_id,
      "vote_info": vote_info,
      "vote_id": vote_id,
      "vote_time": vote_time})
    return True
  except Exception as e:
    print(f"Error saving vote: {e}")
    return False

