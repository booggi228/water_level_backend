from sentinelhub import SHConfig

def login_config(CLIENT_ID, CLIENT_SECRET, instance_id):

    config = SHConfig()
    config.instance_id = instance_id
    
    if CLIENT_ID and CLIENT_SECRET:
        config.sh_client_id = CLIENT_ID
        config.sh_client_secret = CLIENT_SECRET
    if config.sh_client_id == '' or config.sh_client_secret == '' or config.instance_id == '':
        print("Warning! To use Sentinel Hub services, please provide the credentials (client ID and client secret).")
    # config.save()
    return config