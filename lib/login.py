def login_config():

    from sentinelhub import SHConfig
    import json
    with open('./data/Феодосийское.geojson') as f:
        input_json = json.load(f)

    CLIENT_ID = input_json["config"]["client_id"]
    CLIENT_SECRET = input_json["config"]["client_secret"]
    
    config = SHConfig()
    config.instance_id = input_json["config"]["instance_id"]
    
    if CLIENT_ID and CLIENT_SECRET:
        config.sh_client_id = CLIENT_ID
        config.sh_client_secret = CLIENT_SECRET
    if config.sh_client_id == '' or config.sh_client_secret == '' or config.instance_id == '':
        print("Warning! To use Sentinel Hub services, please provide the credentials (client ID and client secret).")
    # config.save()
    return config