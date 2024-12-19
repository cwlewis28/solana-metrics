import solana
import requests
import math
import time

from solana.rpc.api import Client


def get_vote_credits(host):
    client = Client(host)
    epoch = client.get_epoch_info().value.epoch
    accounts = client.get_vote_accounts()

    validators = {}

    for account in accounts.value.current + accounts.value.delinquent:
        try:
            validators[str(account.node_pubkey)] = [i[1] for i in account.epoch_credits if i[0] == epoch][0]
        except IndexError:
            validators[str(account.node_pubkey)] = 0

    return validators


def send_vote_credits_to_pushgateway(host):
    while True:
        cluster_name = host.split("//")[1].split(".")[1]
        validators = get_vote_credits(host)

        for validator, credits in validators.items():
            url = f"http://{cluster_name}-pushgateway:9091/metrics/job/solana_validator/instance/{validator}"
            data = (
                f'solana_validator_credits{{identityPubkey="{validator}"}} {credits}\n'
            )
            response = requests.post(url, data=data)

        average = sum(validators.values()) / len(validators)
        url = f"http://{cluster_name}-pushgateway:9091/metrics/job/solana_validator/instance/average"
        data = f'solana_validator_credits{{identityPubkey="average"}} {average}\n'
        response = requests.post(url, data=data)

        print(f"Pushed validator credits to Pushgateway")

        time.sleep(300)


if __name__ == '__main__':
    send_vote_credits_to_pushgateway('https://api.testnet.solana.com')