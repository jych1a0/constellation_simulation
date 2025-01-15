import json
import re
import os
def update_parameter(params, config_path=None,process_name=None):
    """
    動態調整 parameter 的函式
    
    :param params: 原先的 parameter (dict)
    :param config_path: (可選) 外部設定檔路徑，裡面可定義要移除/重命名/覆寫的規則
    :return: 調整後的 parameter (dict)
    """

    # 1. 從外部檔案讀取 config（若有需要）
    #    假設外部 JSON 結構舉例如下：
    #    {
    #       "remove_keys": ["simEndTime"],
    #       "rename_keys": {
    #           "minLatitude": "myMinLatitude"
    #       },
    #       "override_values": {
    #           "myMinLatitude": "-100"
    #       }
    #    }
    remove_keys = []
    rename_keys = {}
    override_values = {}

    if config_path and os.path.exists(config_path):
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
            process_config = config.get(process_name, {})
            remove_keys = process_config.get("remove_keys", [])
            rename_keys = process_config.get("rename_keys", {})
            override_values = process_config.get("override_values", {})

    # 2. 先針對「移除」的 key 進行處理
    for key_to_remove in remove_keys:
        if key_to_remove in params:
            del params[key_to_remove]

    # 3. 因為要「重新命名」的緣故，需要避免在迴圈中改動 dict，
    #    所以我們先做一個臨時 dict 來承接新的結果
    updated_params = {}

    for k, v in params.items():
        new_key = k
        new_value = v

        # (a) 若此 key 在 rename_keys 中，則改成新的 key
        if k in rename_keys:
            new_key = rename_keys[k]

        # (b) 針對 TLE_inputFileName 做特殊處理
        if new_key == "TLE_inputFileName" and isinstance(new_value, str):
            # 可以用正則取得前面幾位數字
            match = re.search(r'TLE_(\d+)P', new_value)  
            if match:
                number_str = match.group(1)  # 6 / 12 / ...
                if number_str.isdigit():
                    new_value = f'{number_str} * 22'

        # (c) 若此(新)key 在 override_values 中，則直接覆蓋
        if new_key in override_values:
            new_value = override_values[new_key]

        updated_params[new_key] = new_value

    return updated_params

