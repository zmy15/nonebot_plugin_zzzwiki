import os
import json
import nonebot
import yaml
import difflib
from .config import Config
from nonebot.permission import SUPERUSER
from nonebot import on_endswith, on_command
from nonebot.adapters.onebot.v11 import Bot, Event, MessageSegment
from .resource import git_clone, git_pull

guide_image = on_endswith("攻略", ignorecase=False)
pokedex_image = on_endswith("图鉴", ignorecase=False)
download_resources = on_command("下载zzz资源", permission=SUPERUSER, block=True)
update_resources = on_command("更新zzz资源", permission=SUPERUSER, block=True)

global_config = nonebot.get_driver().config
config = Config.parse_obj(global_config.dict())

repo_url = 'https://github.com/Nwflower/zzz-atlas.git'
resources_path = config.resources_path


def load_path():
    file_name = 'path.json'
    file_path = os.path.join(resources_path, file_name)
    if not os.path.exists(file_path):
        try:
            git_pull(resources_path)
        except:
            git_clone(repo_url, resources_path)
    # 读取 path.json 文件
    with open(file_path, 'r', encoding='utf-8') as f:
        path_data = json.load(f)
    return path_data


# 读取角色别名
def load_aliases(file_name):
    file_path = os.path.join(resources_path, file_name)
    with open(file_path, 'r', encoding='utf-8') as f:
        aliases = yaml.safe_load(f)
    return aliases


# 获取别名文件路径，并加载别名数据
aliases_path_guide = load_path()['othername']['角色攻略']
aliases_guide = load_aliases(aliases_path_guide.lstrip('/'))

aliases_path_audio = load_path()['othername']['音擎']
aliases_audio = load_aliases(aliases_path_audio.lstrip('/'))


# aliases_path_record = path_data['othername']['驱动盘']
# aliases_record = load_aliases(aliases_path_audio.lstrip('/'))

@download_resources.handle()
async def handle_download_resources(bot: Bot, event: Event):
    if git_clone(repo_url, resources_path):
        await bot.send(event, "资源下载成功")
    else:
        await bot.send(event, "资源下载失败")


@update_resources.handle()
async def handle_update_resources(bot: Bot, event: Event):
    if git_pull(resources_path):
        await bot.send(event, "资源更新成功")
    else:
        await bot.send(event, "资源更新失败")


@guide_image.handle()
async def handle_send_image(bot: Bot, event: Event):
    # 获取消息文本并去掉“攻略”两个字
    message_text = event.get_message().extract_plain_text().strip()
    if message_text.endswith("攻略"):
        character_name = message_text[:-2].strip()

        # 收集所有角色名及别名进行模糊匹配
        all_names = list(load_path()['角色攻略'].keys()) + sum(filter(None, aliases_guide.values()), [])
        closest_matches = difflib.get_close_matches(character_name, all_names, n=1, cutoff=0.6)
        if closest_matches:
            matched_name = closest_matches[0]
            for main_name, alias_list in aliases_guide.items():
                if matched_name == main_name or matched_name in (alias_list or []):
                    character_name = main_name
                    break
            else:
                character_name = matched_name
        else:
            return

        # 获取图片路径
        if character_name in load_path()['角色攻略']:
            image_path = load_path()['角色攻略'][character_name].lstrip('/')
            full_image_path = os.path.join(resources_path, image_path).replace('/', '\\')
            if os.path.exists(full_image_path):
                await bot.send(event, MessageSegment.image(f"file:///{full_image_path}"))
            else:
                await bot.send(event, f"未找到 {character_name} 的攻略图片。")


@pokedex_image.handle()
async def handle_send_pokedex_image(bot: Bot, event: Event):
    message_text = event.get_message().extract_plain_text().strip()
    if message_text.endswith("图鉴"):
        name = message_text[:-2].strip()

        # 收集所有角色名及别名进行模糊匹配
        all_names = (list(load_path()['角色'].keys()) + list(load_path()['音擎'].keys())
                     + sum(filter(None, aliases_guide.values()), [])
                     + sum(filter(None, aliases_audio.values()), []))
        closest_matches = difflib.get_close_matches(name, all_names, n=1, cutoff=0.6)
        if closest_matches:
            matched_name = closest_matches[0]
            for main_name, alias_list in aliases_audio.items():
                if matched_name == main_name or matched_name in alias_list:
                    name = main_name
                    break
            else:
                name = matched_name

            if name in load_path()['角色']:
                await send_image(bot, event, "角色", name)
            elif name in load_path()['音擎']:
                await send_image(bot, event, "音擎", name)
            # elif name in path_data['驱动盘']:
            #     await send_image(bot, event, "驱动盘", name)


async def send_image(bot: Bot, event: Event, category: str, name: str):
    if name in load_path()[category]:
        image_path = load_path()[category][name].lstrip('/')
        full_image_path = os.path.join(resources_path, image_path).replace('/', '\\')
        if os.path.exists(full_image_path):
            await bot.send(event, MessageSegment.image(f"file:///{full_image_path}"))
