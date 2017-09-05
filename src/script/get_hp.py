import redis
DATA_HOST='127.0.0.1'
DATA_DBID=1
red = redis.StrictRedis(host=DATA_HOST, port='6379', db=DATA_DBID)
zone_list = [1, 2, 3, 100, 101, 200, 201, 300]
for one in zone_list:
	hp_dict = red.hgetall('hp:%s' % one)
	for x, y in hp_dict.items():
		#print x, y, #int(str(y)[:-4]+ str(y)[-4:].zfill(5))
		red.hset('hp:%s' % one, x, int(str(y)[:-4]+ str(y)[-4:].zfill(5)))
	

