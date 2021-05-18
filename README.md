下述文件来源于A岛匿名版(adnmb3.com)，个别文件稍作修改:

- static/css/h.desktop.css
- static/css/uikit.almost-flat.min.css
- static/css/uikit.min.css
- static/img/reed.jpg

# MyChan匿名板

![index](https://raw.githubusercontent.com/VilTea/GraduateProject/raw/master/Image/index.png)

基于python3.8开发，简单的匿名板，基于redis实现了简单的缓存机制。

![board](https://raw.githubusercontent.com/VilTea/GraduateProject/raw/master/Image/board.png)

## 开发环境

- PyCharm 2020.2.1(Community Edition)
- mongodb(4.2.6)
- redis(5.0.10)

## 配置文件

conf/config.json

```json
{
	"DATABASE": {
		"host": "localhost",	//mongo地址
		"port": 27017,			//mongo端口
		"dbname": "mychandb",	//mychan匿名板数据库名
		"collection":{
			"admin": "admin",		//管理员数据文档
			"user": "user",			//用户数据文档
			"section": "section",	//论坛分区数据文档
			"stage": "stage",		//串数据文档
			"log": "log"			//日志文档
		}
	},
	"CACHEBASE": {
		"host": "localhost",	//redis地址
		"port": "6379",			//redis端口
		"maxsize_NQ": 15,		//常驻先进先出队列最大尺寸
		"expire_THC": 300,		//临时缓存数据过期时间
		"ask_time_THC": 50,		//非缓存数据请求计数器存在时长
		"max_ask_THC": 5		//非缓存数据最大计数，达到此计数的数据会被塞入临时缓存队列
	},
	"DEBUG": true				//DEBUG模式
}
```

