import pika
import ssl

# Establish a connection to the RabbitMQ server
# context = ssl._create_unverified_context()

context = ssl.create_default_context(
    cafile="/home/ubuntu/workspace/python/python_rabbit/rabbit_producer_consumer/setup/ssl2/ca-cert.pem")
context.load_verify_locations(cafile="/home/ubuntu/workspace/python/python_rabbit/rabbit_producer_consumer/setup/ssl2/ca-cert.pem")
context.verify_mode = ssl.CERT_REQUIRED
context.load_cert_chain(certfile="/home/ubuntu/workspace/python/python_rabbit/rabbit_producer_consumer/setup/ssl2/client-cert.pem",
                        keyfile="/home/ubuntu/workspace/python/python_rabbit/rabbit_producer_consumer/setup/ssl2/client-key.pem")
ssl_options = pika.SSLOptions(context, "mycompany.com")
conn_parameters = pika.ConnectionParameters(ssl_options=ssl_options,host='localhost', port=5671, virtual_host='/', credentials=pika.PlainCredentials('guest', 'guest'))

#connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
connection = pika.BlockingConnection(conn_parameters)

# Create a channel on this connection
channel = connection.channel()

# Declare a queue where the message will be published
# channel.queue_declare(queue='hello',durable=True)

# Publish the message to the queue
headers = {'key1': 'value1', 'key2': 'value2'}
properties = pika.BasicProperties(delivery_mode=2, app_id='pub1', reply_to='profiler-update',headers=headers)
if channel.is_open:
    for i in range(2):
        channel.basic_publish(properties=properties,exchange='profile-update-Ex', routing_key='profiler-update', body=bytes('Hello World {}23'.format(i),'utf-8'))

print(" [x] Sent 'Hello World!'")

# Close the channel and the

channel.close()
connection.close()