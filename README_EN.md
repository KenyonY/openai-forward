[**中文**](./README.md) | **English**

<h1 align="center">
    <br>
    OpenAI Forward
    <br>
</h1>
<p align="center">
    <b> OpenAI API 接口转发服务 <br/>
    The fastest way to deploy openai api forward proxy </b>
</p>

<p align="center">
    <a href="https://pypi.org/project/openai-forward/">
        <img alt="pypi" src="https://img.shields.io/badge/pypi-0.0.8-green.svg">
    </a>
    <a href="https://github.com/beidongjiedeguang/openai-forward/blob/main/LICENSE">
        <img alt="License" src="https://img.shields.io/github/license/beidongjiedeguang/openai-forward.svg?color=blue&style=flat-square">
    </a>
    <a href="https://github.com/beidongjiedeguang/openai-forward/releases">
        <img alt="Release (latest by date)" src="https://img.shields.io/github/v/release/beidongjiedeguang/openai-forward">
    </a>
    <a href="https://github.com/beidongjiedeguang/openai-forward">
        <img alt="GitHub repo size" src="https://img.shields.io/github/repo-size/beidongjiedeguang/openai-forward">
    </a>
    <a href="https://github.com/beidongjiedeguang/openai-forward/">
        <img alt="GitHub top language" src="https://img.shields.io/github/languages/top/beidongjiedeguang/openai-forward">
    </a>
    <a href="https://github.com/beidongjiedeguang/openai-forward/actions/workflows/run_tests.yaml">
        <img alt="tests" src="https://img.shields.io/github/actions/workflow/status/beidongjiedeguang/openai-forward/run_tests.yml?label=tests">
    </a>
    <a href="=https://pypi.org/project/openai_forward/">
        <img alt="pypi downloads" src="https://img.shields.io/pypi/dm/openai_forward">
    </a>
    <a href="=https://codecov.io/gh/beidongjiedeguang/openai-forward">
        <img alt="codecov" src="https://codecov.io/gh/beidongjiedeguang/openai-forward/branch/main/graph/badge.svg">
    </a>
</p>

解决国内无法直接访问OpenAI的问题，将该服务部署在海外服务器上，通过该服务转发OpenAI的请求。即搭建反向代理服务  
测试访问：https://caloi.top/v1/chat/completions 将完全等价于 https://api.openai.com/v1/chat/completions

# Table of Contents
- [特点](##特点)
- [应用](##应用)
- [服务部署](##服务部署)
- [服务调用](##服务调用)
- [Https 支持](##Https 支持)