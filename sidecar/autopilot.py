import socket, requests, uuid, click, json, time, signal


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
    service_id = "{0}-{1}".format(service, uuid.uuid4().hex)
    proxy_id = "{0}-proxy-{1}".format(service, uuid.uuid4().hex)

    with open('/usr/app/service.id', 'w') as file:
      file.write(service_id)
    with open('/usr/app/proxy.id', 'w') as file:
      file.write(proxy_id)
  

    def sigterm(x, y):
  
      print('[python] SIGTERM received, time to leave.')
      c.deregister(service_id)
      c.deregister(proxy_id)
      running = False
      # exit()

    # Register the signal to the handler
    signal.signal(signal.SIGTERM, sigterm)  # Used by this script

    public_listener_sample = {
      "name": "public_listener:0.0.0.0:8000",
      "address": {
        "socketAddress": {
          "address": "0.0.0.0",
          "portValue": 8000
        }
      },
      "filterChains": [
        {
          "filters": [
            {
              "name": "envoy.http_connection_manager",
              "config": {
                "tracing": {
                  "operation_name": "ingress"
                },
                "access_log": [
                  {
                    "name": "envoy.file_access_log",
                    "config": {
                      "path": "/dev/stdout",
                      "format": "[ACCESS_LOG][%START_TIME%] \"%REQ(:METHOD)% %REQ(X-ENVOY-ORIGINAL-PATH?:PATH)% %PROTOCOL%\" %RESPONSE_CODE% %RESPONSE_FLAGS% %BYTES_RECEIVED% %BYTES_SENT% %DURATION% %RESP(X-ENVOY-UPSTREAM-SERVICE-TIME)% \"%REQ(X-FORWARDED-FOR)%\" \"%REQ(USER-AGENT)%\" \"%REQ(X-REQUEST-ID)%\" \"%REQ(:AUTHORITY)%\" \"%UPSTREAM_HOST%\" \"%DOWNSTREAM_REMOTE_ADDRESS_WITHOUT_PORT%\"\n"
                    }
                  }
                ],
                "stat_prefix": "public_listener",
                "route_config": {
                  "name": "local_route",
                  "virtual_hosts": [
                    {
                      "name": "local",
                      "domains": ["*"],
                      "routes": [
                        {
                          "match": {
                            "prefix": "/"
                          },
                          "route": {
                            "cluster": "local_app"
                          },
                          "decorator": {
                            "operation": "checkAvailability"
                          }
                        }
                      ]
                    }
                  ]
                },
                "http_filters": [
                  {
                    "name": "envoy.router",
                    "config": {}
                  }
                ]
              }
            }
          ]
        }
      ]
    }

    proxy_routes = [
      {
        "match": {
          "prefix": "/service1"
        },
        "route": {
          "cluster": "service:service1"
        },
        "decorator": {
          "operation": "checkStock"
        }
      },
      {
        "match": {
          "prefix": "/service2"
        },
        "route": {
          "cluster": "service:service2"
        },
        "decorator": {
          "operation": "checkStock"
        }
      }
    ]

    proxy_listener_sample = {
      "name": "proxy_listener:127.0.0.1:80",
      "address": {
        "socketAddress": {
          "address": "127.0.0.1",
          "portValue": 80
        }
      },
      "filterChains": [
        {
          "filters": [
            {
              "name": "envoy.http_connection_manager",
              "config": {
                "tracing": {
                  "operation_name": "egress"
                },
                "access_log": [
                  {
                    "name": "envoy.file_access_log",
                    "config": {
                      "path": "/dev/stdout",
                      "format": "[ACCESS_LOG][%START_TIME%] \"%REQ(:METHOD)% %REQ(X-ENVOY-ORIGINAL-PATH?:PATH)% %PROTOCOL%\" %RESPONSE_CODE% %RESPONSE_FLAGS% %BYTES_RECEIVED% %BYTES_SENT% %DURATION% %RESP(X-ENVOY-UPSTREAM-SERVICE-TIME)% \"%REQ(X-FORWARDED-FOR)%\" \"%REQ(USER-AGENT)%\" \"%REQ(X-REQUEST-ID)%\" \"%REQ(:AUTHORITY)%\" \"%UPSTREAM_HOST%\" \"%DOWNSTREAM_REMOTE_ADDRESS_WITHOUT_PORT%\"\n"
                    }
                  }
                ],
                "generate_request_id": "true",
                "stat_prefix": "proxy_listener",
                "route_config": {
                  "name": "proxy_route",
                  "virtual_hosts": [
                    {
                      "name": "proxy",
                      "domains": ["*"],
                      "routes": proxy_routes
                    }
                  ]
                },
                "http_filters": [
                  {
                    "name": "envoy.router",
                    "config": {}
                  }
                ]
              }
            }
          ]
        }
      ]
    }

    local = {
      "name": service,
      "id": service_id,
      "port": 8080,
      "address": ip,
      "checks": [
        {
          "Name": "Service Listening ({0})".format(service),
          "TCP": "{0}:8080".format(ip),
          "Interval": "10s"
        }
      ],
    }

    proxy = {
      "name": "{0}-sidecar-proxy".format(service),
      "id": proxy_id,
      "port": 8000,
      "address": ip,
      "kind": "connect-proxy",
      "checks": [
        {
          "Name": "Connect Proxy Listening ({0})".format(service),
          "TCP": "{0}:8000".format(ip),
          "Interval": "10s"
        }
      ],
      "proxy": {
        "destination_service_name": service,
        "destination_service_id": service_id,
        "local_service_address": "127.0.0.1",
        "local_service_port": 8080,
        "config": {
          "envoy_public_listener_json": json.dumps(public_listener_sample)
        },
        "upstreams": [
          {
            # "destination_name": "local_app",
            "local_bind_port": 80,
            "config": {
              "envoy_listener_json": json.dumps(proxy_listener_sample)
            }
          },
          {
            "destination_name": "service1",
            "local_bind_port": 18005,
          },
          {
            "destination_name": "service2",
            "local_bind_port": 18006,
          }
        ]
      }
    }

    if (c.consul_conn_check()):
      c.register(local)
      c.register(proxy)
      print('registered')
      print('[python] Started, waiting for SIGTERM')
      # while True:
      #     if running:
      #         time.sleep(1)
      #     else:
      #         break

      # print('[python] Bye...')
    else:
      print('no connection...')


cli.add_command(start)


if __name__ == '__main__':
    cli()
    
