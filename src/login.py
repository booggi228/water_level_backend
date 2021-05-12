def login_config():

    from sentinelhub import SHConfig

    CLIENT_ID = '705de065-d047-4187-b8d2-01386b232165'
    CLIENT_SECRET = 'U3n%1|B*pa@GvjA}UvxgyO@!RT-o}C}r1T?#7SwN'
    
    config = SHConfig()
    config.instance_id = '274430c0-0c82-493a-95c6-694e4640cf14'
    
    if CLIENT_ID and CLIENT_SECRET:
        config.sh_client_id = CLIENT_ID
        config.sh_client_secret = CLIENT_SECRET
    if config.sh_client_id == '' or config.sh_client_secret == '' or config.instance_id == '':
        print("Warning! To use Sentinel Hub services, please provide the credentials (client ID and client secret).")
    # config.save()
    return config