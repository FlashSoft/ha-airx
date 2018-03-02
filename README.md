# HA-AIRX
`airx的home assistant插件`

#### 配置修改

需要在configuration.yaml中开启packages
```yaml
homeassistant:
  packages: !include_dir_named packages
```




需要自己根据自己的情况修改airx.yaml和secrets.yaml
获取自己的token、userid、deviceid办法
https://bbs.hassbian.com/thread-2113-1-1.html

```yaml
airx_token: 0000000000000
airx_user_id: 111111
airx_device_id: 22222
airx_device2_id: 22222
```
#### 变更记录
```
0.01
	第一版，功能跑通
0.02
	新增设备所在区域户外PM2.5的值显示，方便做一些联动
	新增屏幕以及儿童锁的状态显示
	调整控制器逻辑
	新增可见状态同步，如果token等信息配置不正确，设备会变成不可用
```


效果

![图片](https://wx1.sinaimg.cn/large/56e89fd7ly1foydn9uyysj20en0ehjs5.jpg)

![图片](https://wx3.sinaimg.cn/large/56e89fd7ly1foydnyozc8j20b90awmxk.jpg)
