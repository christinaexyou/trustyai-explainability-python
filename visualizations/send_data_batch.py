import json
import subprocess
import time

def send_data_batch(batch_file):
    with open(batch_file) as f:
        data = json.load(f)
        NFILES = len(data['inputs'][0]['data'])

    alpha_model = 'demo-loan-nn-onnx-alpha'
    beta_model = 'demo-loan-nn-onnx-beta'

    odh_project = 'opendatahub'
    model_namespace = 'model-namespace'

    # make sure we are on the `model-namespace` project
    subprocess.run(f'oc project {model_namespace}', shell=True)

    # get trustyai pod
    model_namespace_pods = subprocess.check_output('oc get pods -o name', shell=True).decode().split('\n')
    trusty_pod = [pod for pod in model_namespace_pods if 'trustyai-service' in pod][0]

    alpha_infer_route = subprocess.check_output(f'oc get route {alpha_model}' + ' --template={{.spec.host}}{{.spec.path}}', shell=True).decode()
    beta_infer_route = subprocess.check_output(f'oc get route {beta_model}' + ' --template={{.spec.host}}{{.spec.path}}', shell=True).decode()

    def check_for_reception(percent, model_name, threshold=950, max_retries=4):
        checks = 0 
        while True:
            thresh = int(percent * threshold / 1000)
            n_obs = get_counter(model_name)
            print(f'Making sure TrustyAI {model_name} dataset contains at least {thresh} points, has {n_obs} (tried {checks} times)', end='')
            if checks >= max_retries:
                print(' [timeout]')
                exit(1)
            elif n_obs > thresh:
                break
            else:
                checks += 1
                time.sleep(1)
        print(' [done]')

    def get_counter(model_name):
        file_present = subprocess.run(['oc', 'exec',  trusty_pod, '-c', 'trustyai-service',  '--', 'bash', '-c', f"ls /inputs/ | grep {model_name} || echo ''"], stdout=subprocess.PIPE, text=True).stdout.strip()
        if not file_present:
            return 0 
        else:
            obs = json.loads(subprocess.run(['oc', 'exec', trusty_pod, '-c', 'trustyai-service', '--', 'bash', '-c', f'cat /inputs/{model_name}-metadata.json'], stdout=subprocess.PIPE, text=True).stdout.strip())['observations']
            return int(obs) if obs else 0
    
    START_OBS_ALPHA = get_counter(alpha_model)
    print(f'{START_OBS_ALPHA} datapoints already in ALPHA dataset')
    START_OBS_BETA = get_counter(beta_model)
    print(f'{START_OBS_BETA} datapoints already in BETA dataset')

    tries = 0 
    success_alpha = False
    success_beta = False

    # for batch in range(0, 2551, 250):
  
    while not (success_alpha and success_beta):
        if tries > 4:
            print(f'\nError: Send data batch timeout')
            exit(1)
        else:
            print(f'Data batch transmission (ATTEMPT {tries})')

        if not success_alpha:
            subprocess.run(['curl', '-k', f'https://{alpha_infer_route}/infer', '-d', f'@{batch_file}'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, text=True)
            check_for_reception(len(data['inputs'][0]['data']) + START_OBS_ALPHA, alpha_model)
            success_alpha = True

        if not success_beta:
            subprocess.run(['curl', '-k', f'https://{beta_infer_route}/infer', '-d', f'@{batch_file}'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, text=True)
            check_for_reception(len(data['inputs'][0]['data']) + START_OBS_BETA, beta_model)
            success_beta = True
            
        tries += 1