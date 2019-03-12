import socket, requests, click, time, signal


def get_ip_address():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(('8.8.8.8', 80))
    return s.getsockname()[0]    


class Client(object):

    def __init__(self, endpoint='http://localhost:8500'):
        self.endpoint = endpoint
        
        self.url_register = '{}/{}'.format(self.endpoint, 'v1/agent/service/register')
        self.url_deregister = '{}/{}'.format(self.endpoint, 'v1/agent/service/deregister')
        self.url_services = '{}/{}'.format(self.endpoint, '/v1/catalog/services')
        self.url_service = '{}/{}'.format(self.endpoint, '/v1/catalog/service')
        self.url_nodes = '{}/{}'.format(self.endpoint, '/v1/catalog/nodes')
        self.url_node = '{}/{}'.format(self.endpoint, '/v1/catalog/node')
 
    def consul_conn_check(self):
        state = False
        try:
            r = requests.get(self.url_nodes)
            state = True
        except requests.ConnectionError:
            pass
        finally:
            return state

    def register(self, service):
        print(json.dumps(service))
        """Register a new service with the local consul agent"""
        r = requests.put(self.url_register, json=service)
        if r.status_code != 200:
            raise Exception(
                'PUT returned {}'.format(r.status_code))
        return r

    def deregister(self, id):
        """Deregister a service with the local consul agent"""
        r = requests.put('{}/{}'.format(self.url_deregister, id))
        if r.status_code != 200:
            raise Exception(
                'PUT returned {}'.format(r.status_code))
        return r


@click.group(help='')
def cli():
    pass


@click.command()
@click.option('-s', '--service', help='service name', required=True, type=str)
@click.option('-p', '--port', help='', default=8080, type=int)
@click.option('-c', '--consul-host', help='', type=str)
def start(service, port, consul_host):

    running = True
    c = Client(consul_host)
    ip = get_ip_address()
   
    with open('/usr/app/service.id', 'r') as file:
      service_id = file.read().replace('\n', '')

    with open('/usr/app/proxy.id', 'r') as file:
      proxy_id = file.read().replace('\n', '')
   
  

    def cleanup(sigid, frame):
  
      print('[python] {0} received, time to leave.'.format(sigid))
      c.deregister(service_id)
      c.deregister(proxy_id)
      print('deregistered...')
      running = False
      exit()

    # Register signal handler
    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)
    signal.signal(signal.SIGUSR1, cleanup)

    print('[python] Started watch, waiting for SIGTERM')
    while True:
        if running:
            time.sleep(1)
        else:
            break

    print('[python] Bye...')


cli.add_command(start)


if __name__ == '__main__':
    cli()
    
