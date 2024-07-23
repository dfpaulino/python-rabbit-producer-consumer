import ssl
import threading
import time

import pika
from pika.exceptions import ConnectionClosedByBroker, AMQPConnectionError, ChannelWrongStateError


class Task(threading.Thread):
    def __init__(self, id: int):
        super().__init__()
        context = ssl.create_default_context(
            cafile="/home/ubuntu/workspace/python/python_rabbit/rabbit_producer_consumer/setup/ssl2/ca-cert.pem")
        context.load_verify_locations(cafile="/home/ubuntu/workspace/python/python_rabbit/rabbit_producer_consumer/setup/ssl2/ca-cert.pem")
        context.verify_mode = ssl.CERT_REQUIRED
        context.load_cert_chain(certfile="/home/ubuntu/workspace/python/python_rabbit/rabbit_producer_consumer/setup/ssl2/client-cert.pem",
                                keyfile="/home/ubuntu/workspace/python/python_rabbit/rabbit_producer_consumer/setup/ssl2/client-key.pem")
        ssl_options = pika.SSLOptions(context, "mycompany.com")
        parameter = pika.ConnectionParameters(ssl_options=ssl_options, host='localhost', port=5671,
                                              virtual_host='/',
                                              credentials=pika.PlainCredentials('guest', 'guest'))

        # parameter = pika.URLParameters("amqp://guest:guest@localhost:5672/%2F")
        self.connection = pika.BlockingConnection(parameter)
        self.channel = self.connection.channel()
        self.channel.basic_qos(prefetch_count=10)
        self.channel.basic_consume(queue='profiler-update-Q', on_message_callback=self.callback, auto_ack=False)
        self.id = id
        self.event_is_stopped = threading.Event()
        self._message_count = 0
        # threading.Thread(target=self.run, daemon=True).start()

    def reconnect(self):
        try:
            if self.channel.is_open:
                self.channel.close()
            if self.connection.is_open:
                self.connection.close()
            context = ssl.create_default_context(
                cafile="/home/ubuntu/workspace/docker/mongoAndRabbit/ssl2/ca-cert.pem")
            context.load_verify_locations(cafile="/home/ubuntu/workspace/docker/mongoAndRabbit/ssl2/ca-cert.pem")
            context.verify_mode = ssl.CERT_REQUIRED
            context.load_cert_chain(certfile="/home/ubuntu/workspace/docker/mongoAndRabbit/ssl2/client-cert.pem",
                                    keyfile="/home/ubuntu/workspace/docker/mongoAndRabbit/ssl2/client-key.pem")
            ssl_options = pika.SSLOptions(context, "mycompany.com")
            parameter = pika.ConnectionParameters(ssl_options=ssl_options, host='localhost', port=5671,
                                                  virtual_host='/',
                                                  credentials=pika.PlainCredentials('guest', 'guest'))

            # parameter = pika.URLParameters("amqp://guest:guest@localhost:5672/%2F")
            self.connection = pika.BlockingConnection(parameter)
            self.channel = self.connection.channel()
            self.channel.basic_qos(prefetch_count=10)
            self.channel.basic_consume(queue='profiler-update-Q', on_message_callback=self.callback, auto_ack=False)
        except Exception as e:
            print(e)

    def callback(self, ch, method, properties, body):
        print('Thread Id {}'.format(self.id))
        print('appId {},reply_to {}, headers {}'.format(properties.app_id, properties.reply_to, properties.headers))
        print('header key1 {}'.format(properties.headers['key1']))
        time.sleep(0.1)
        print(" [x] Received %r" % body)
        self._message_count += 1
        ch.basic_ack(delivery_tag=method.delivery_tag)


    def run(self) -> None:
        while self.event_is_stopped.is_set() is False:
            try:
                if self.channel.is_open:
                    print('Thread Id {} start consuming'.format(self.id))
                    self.channel.start_consuming()
                else:
                    raise AMQPConnectionError

            except (ConnectionClosedByBroker, AMQPConnectionError, ssl.SSLEOFError, ChannelWrongStateError) as err:
                print(err.with_traceback(None))
                print('exception block...')
                if self.event_is_stopped.is_set() is False:
                    print('Thread Id {} reconnect'.format(self.id))
                    time.sleep(10)
                    self.reconnect()

        print('Thread Id {} stopping'.format(self.id))

    def get_message_count(self):
        return self._message_count

    def stop(self):
        """Stop listening for jobs"""
        self.connection.add_callback_threadsafe(self._stop)
        self.join()
    def _stop(self):
        self.event_is_stopped.set()
        self.channel.stop_consuming()
        #self.channel.close()
        self.connection.close()


workers = []
for i in range(4):
    t = Task(i)
    workers.append(t)
    t.start()

time.sleep(60)

for w in workers:
    print('stop')
    try:
        w.stop()
    except Exception as e:
        print('trying to stop')
        print(e.with_traceback(None))

time.sleep(10)
total_messages = 0
for w in workers:
    try:
        # w.join(timeout=1.0)
        print('Thread {} with msg count {}'.format(w.id, w.get_message_count()))
        total_messages += w.get_message_count()
    except Exception as e:
        print('trying to join')
        print(e.with_traceback(None))

print('Total messages {}'.format(total_messages))
# Start consuming messages from the queue using the callback function
# channel.start_consuming()
