# Tiance Themes

天策官方在线主题仓库。

仓库只保存可公开分发的主题内容，不保存用户本地分类、排序、项目 ID、当前主题或 `.Tiance` 工作区数据。

## 主题包结构

```text
themes/<theme-id>/
├─ manifest.json
├─ theme.json
├─ preview.webp
└─ assets/
```

- `theme.json`：天策主题运行合同，当前要求 `schemaVersion: 2`，并以 `registrationName` 提供首次安装时的注册显示名称。
- `manifest.json`：版本、作者、简介、许可证、基色标签和兼容范围。
- `preview.webp`：在线市场使用的轻量预览图。
- `assets/`：主题背景等本地资源。

在线市场不定义用户分类。主题安装时由用户选择自己的本地主题分类。

## 收录要求

- 主题目录名必须与 `theme.json.id` 一致。
- 背景资源必须使用 `assets/...` 相对路径。
- 主题包不得包含 `.Tiance`、`catalog.json`、`theme-settings.json`、会话或绝对路径。
- 每次发布必须使用明确版本，并通过仓库校验后生成市场索引和固定版本安装包。

## 许可证

仓库内容采用 [CC0 1.0 Universal](https://creativecommons.org/publicdomain/zero/1.0/)，允许任何人复制、修改、分发和商用，无需申请许可。
