# XiaoTu Door(小兔开门) Custom Component For Home Assistant

此项目是 Home Assistant 平台 XiaoTu Door(小兔开门) 的自定义组件的集成实现。

组件基于 XiaoTu Door 微信小程序相关接口实现，暂时不支持帐号登录（验证码问题）。

因此，需先登录小兔开门微信小程序，并需要手动抓取 `openid` 和 `clientId` 参数。

## 支持设备

- 当前仅支持门禁

## 接入方法

1. 将项目 ha-xiaotu-door 目录部署到自定义组件目录，一般路径为 `~/.homeassistant/custom_components/`
2. 通过 [HACS](https://hacs.xyz/) 载入自定义存储库(Custom repositories)
    - 设置URL: https://github.com/laoshu133/ha-xiaotu-door
    - 类别: 集成(Integration)

## 配置方法

本集成已支持 HA 可视化配置，在 `配置-集成-添加集成` 中选择 XiaoTu Door，依次填入 `API Host`, `WeChat OpenId`, `XiaoTu ClientId` 即可。

## License

MIT
