import io
import re
import pandas as pd
import numpy as np
import ipywidgets as widgets
from ipywidgets import Layout
import warnings

def prompt_upload():
    uploader = widgets.FileUpload(description="Upload Coding Confirmation (.xlsx)", layout=Layout(width="270px"), multiple=False)
    display(uploader)

    main_display = widgets.Output()

    def on_upload_change(inputs):
        with main_display:
            main_display.clear_output()
            display(list(inputs['new'].keys())[-1])

    uploader.observe(on_upload_change, names='value')
    return [uploader, main_display]

def load_from_widget(uploader_in, header=5, sheet_name="AE"):
    '''
    Release function to load file
    '''
    uploaded_file = uploader_in.value
    file_name = list(uploaded_file.keys())[0]
    df = pd.read_excel(io.BytesIO(uploaded_file[file_name]["content"]),
                       header=header,
                       sheet_name=sheet_name)
    
    colnames = ["이상사례명(MedDRA_SOC_ENG)","이상사례명(MedDRA_SOC_KOR)",
            "이상사례명(MedDRA_PT_ENG)","이상사례명(MedDRA_PT_KOR)",
            "Expectedness","차수","중대성","ADR 여부", "자료원"]
    
    df = df[colnames]
    
    df["SOC"] = df["이상사례명(MedDRA_SOC_ENG)"] + " (" + df["이상사례명(MedDRA_SOC_KOR)"] + ")"
        
    df["PT"] = df["이상사례명(MedDRA_PT_ENG)"] + " (" + df["이상사례명(MedDRA_PT_KOR)"] + ")"
    df = df.drop(columns=["이상사례명(MedDRA_SOC_ENG)",
                              "이상사례명(MedDRA_SOC_KOR)",
                              "이상사례명(MedDRA_PT_ENG)","이상사례명(MedDRA_PT_KOR)"])
    
    
    return df
    
    

def load_format(filename, header=5, sheet_name="AE"):
    '''
    Debugging function to load file
    '''
    
    df = pd.read_excel(filename, header=5, sheet_name="AE")
    
    colnames = ["이상사례명(MedDRA_SOC_ENG)","이상사례명(MedDRA_SOC_KOR)",
            "이상사례명(MedDRA_PT_ENG)","이상사례명(MedDRA_PT_KOR)",
            "Expectedness","차수","중대성","ADR 여부", "자료원"]
    
    df = df[colnames]
    
    df["SOC"] = df["이상사례명(MedDRA_SOC_ENG)"] + " (" + df["이상사례명(MedDRA_SOC_KOR)"] + ")"
        
    df["PT"] = df["이상사례명(MedDRA_PT_ENG)"] + " (" + df["이상사례명(MedDRA_PT_KOR)"] + ")"
    df = df.drop(columns=["이상사례명(MedDRA_SOC_ENG)",
                              "이상사례명(MedDRA_SOC_KOR)",
                              "이상사례명(MedDRA_PT_ENG)","이상사례명(MedDRA_PT_KOR)"])
    
    
       
    return df


def auto_cleaner(df):
    '''
    Auto cleans trailing and leading whitespace from titles for easier recognition
    '''
    binary_cols = ["Expectedness", "중대성", "ADR 여부", "자료원"]

    for i in range(len(binary_cols)):
        no_nan = [x for x in df[binary_cols[i]] if str(x) != 'nan']
        for old in no_nan:
            new = re.sub("^(\s|[ \t]|[\n])*", "", old)
            new = re.sub("(\s|[ \t]|[\n])*$", "", new)
            
            if new != old:
                df[binary_cols[i]] = df[binary_cols[i]].str.replace(old, new, regex=False)
    

    return df


def process_meddra(df):
    print("Excel MedDRA (SOC, PT) summary")
    
    meddra_cols = ["SOC", "PT"]
    special_chars = ['\t', '\r', '\n', '\v']
    
    for m in meddra_cols:
        cleaned = []
        for text in df[m]:
            no_ws = re.sub("\s{2,}", "", text)
            for c in special_chars:
                no_ws = re.sub(c, "", no_ws)
                
            cleaned.append(no_ws)
        df[m] = cleaned
        print("    {}\n   * ".format(m), end="")
        print(*pd.Series(pd.unique(cleaned)).sort_values(), sep="\n   * ")
    print("*"*40)
    return df

        
def process_binary(df, first_call=True):
    binary_cols = ["Expectedness", "중대성", "ADR 여부", "자료원"]
    edited = list()
    idx = 0
    
    while idx < len(binary_cols):
        cleaned = [x for x in df[binary_cols[idx]] if str(x) != 'nan']
        
        if len(pd.unique(cleaned)) > 2:
            print("Column '{}' is not binary: ".format(binary_cols[idx]), end="")
            print(pd.unique(cleaned))

            choice = input("\t모드를 숫자로 선택 후 'Enter'키로 이동하세요:\n\t1) 제목 삭제 모드 (모든 매치 제거) \n\t2) 제목 수정 모드 (오타인 경우) \n\tEnter: ")
            
            if choice == "1":
                edited.append(idx)
                problem_rows = input("\t\t(정확히) 일치하는 행 제거: " )
                df = df.loc[~df[binary_cols[idx]].str.contains(problem_rows, regex=False, na=True)]
                
                cleaned = [x for x in df[binary_cols[idx]] if str(x) != 'nan']
                if len(pd.unique(cleaned)) > 2:
                    print("Binary 처리 실패. '{}'".format(binary_cols[idx]))
                    print(pd.unique(cleaned))
                    df = process_binary(df, False)

            elif choice == "2":
                edited.append(idx)
                remove = input("\t제거할 문자열: ")
                value = input("\t대체할 문자열: ")
                df[binary_cols[idx]] = df[binary_cols[idx]].str.replace(remove, value, regex=False)
                
                cleaned = [x for x in df[binary_cols[idx]] if str(x) != 'nan']
                if len(pd.unique(cleaned)) > 2:
                    print("Binary 처리 실패. '{}'".format(binary_cols[idx]))
                    print(pd.unique(cleaned))
                    df = process_binary(df, False)
                
            else:
                print("Enter 1 or 2")
                idx -= 1
        idx += 1
        
    if first_call:
        print("*"*40)
        print("Excel column summary")
        for binary in binary_cols:
            cleaned = [x for x in df[binary] if str(x) != 'nan']
            print("    {} : {}".format(binary, pd.unique(cleaned)))
        print("*"*40)
    
    return df

def process_time(df):
    choice = ""
    while (choice != "3"):
        print("Check if 차수 is correct:\n")
    
        print(pd.unique(df["차수"]), end='\n\n')
        choice = input("\t모드를 숫자로 선택 후 'Enter'키로 이동하세요:\n\t1) 제목 삭제 모드 (모든 매치 제거) \n\t2) 제목 수정 모드 (오타인 경우) \n\t3) 확인. 다음 \n\tNumber: ")
        if choice == "1":
            problem_rows = input("\t\t(정확히) 일치하는 행 삭제: " )

            print("*"*40)
            print("Removing following rows...\n")
            print("{}\n\n".format(df.loc[df["차수"].str.contains(problem_rows, regex=True)]))
            print("*"*40)

            df = df.loc[~df["차수"].str.contains(problem_rows, regex=True)]

        elif choice == "2":
            remove = input("\t제거할 문자열: ")
            value = input("\t대체할 문자열: ")
            df["차수"] = df["차수"].str.replace(remove, value, regex=True)
            
        elif choice == "3":
            continue
            
        else:
            print("Enter 1, 2 or 3")

    return df

def clean_list(list_in):
    '''Removes trailing and leading whitespace from each string element in list'''
    new_list = list()
    for old in list_in:
        new = re.sub("^(\s|[ \t]|[\n])*", "", old)
        new = re.sub("(\s|[ \t]|[\n])*$", "", new)
        new_list.append(new)
        
    return new_list

def identify_adrness(df):
    '''
    Identifies adr in [no, yes] order
    '''
    adr_stat = clean_list(pd.unique(df["ADR 여부"]))
    # adr_stat = clean_list(["\tnonADr  "])
    
    yes = ["adr", "에", "예", "yes"]
    no = ["non-adr", "non adr", "아니오", "no", "non"]
    
    found = True
    if len(adr_stat) == 1:
        # If dataset only has one (e.g., ADR), generate the other (e.g., non-ADR) 
        if adr_stat[0].lower() in yes:
            return ["non-ADR", adr_stat[0]]
        elif adr_stat[0].lower() in no or "non" in adr_stat[0].lower():
            return [adr_stat[0], "ADR"]
        else:
            found = False
    else:
        # Otherwise, use what already exists
        if adr_stat[0].lower() in yes:
            if adr_stat[1].lower() not in no and "non" not in adr_stat[1].lower():
                # print("non-ADR '{}'을 [{}]에서 못 찾았어요".format(adr_stat[1], no))
                print("'{}'이 non-ADR 로 진행합니다.".format(adr_stat[1]))
                
                confirm = input("확인? (y/n): ")
                while confirm != "n" and confirm != "y":
                    confirm = input("확인? (y/n): ")
                if confirm == "n":
                    return [adr_stat[0], adr_stat[1]]
            return [adr_stat[1], adr_stat[0]]
        
        
        elif adr_stat[0].lower() in no or "non" in adr_stat[0].lower():
            if adr_stat[1].lower() not in yes:
                # print("ADR '{}'을 [{}]에서 못 찾았어요".format(adr_stat[1], yes))
                print("'{}'이 ADR 로 진행합니다.".format(adr_stat[1]))
                
                confirm = input("확인? (y/n): ")
                while confirm != "n" and confirm != "y":
                    confirm = input("확인? (y/n): ")
                    
                if confirm == "n":
                    return [adr_stat[1], adr_stat[0]]
            return [adr_stat[0], adr_stat[1]]
        
        else:
            found = False

    if not found:
        print("'ADR 여부' column에서 'ADR', 'non-ADR'을 찾지 못했습니다:")
        print("현재 'ADR 여부' column:")
        print(adr_stat)
        print("직접 선택하세요")
        truth = input("'{}'이 'ADR' 맞을까요? (혹은 '{}'이 'non-ADR'). Type y/n ".format(adr_stat[0], adr_stat[1]))
        if truth:
            return [adr_stat[1], adr_stat[0]]
        return [adr_stat[0], adr_stat[1]]




def make_expectedness_key(df):
    '''
    Works with data_processed     
    '''
    df["SOC#PT"] = df["SOC"] + "#" + df["PT"]
    key = df.drop(columns=['차수', '중대성', 'ADR 여부', '자료원', 'SOC', 'PT']).reset_index(drop=True)
    key = key.drop_duplicates("SOC#PT")
    key_cols = key['SOC#PT']
    key = key.T
    key.columns = key_cols
    key = key.reset_index(drop=True)
    key = key.drop(index=1)
    return key

def edit_multilevel_columns(table, pairing, level):
    df = table.copy()
    new_columns = []
    for triple in df.columns:
        triple_new = list(triple)
        if triple[level] in pairing.keys():
            triple_new[level] = pairing[triple[level]]
        new_columns.append(tuple(triple_new))
        
    df.columns = pd.MultiIndex.from_tuples(new_columns, names=df.columns.names)
    return df
    
def identify_seriousness(df):
    '''
    Identifies seriousness in [no, yes] order
    '''
    ser_stat = clean_list(pd.unique(df["중대성"]))
    # ser_stat = clean_list(["nO\t"])
    
    yes = ["예", "에", "yes", "중대한", "중대함"]
    no = ["아니요", "아니오", "no", "중대하지 않은", "중대하지 않함"]
    
    found = True
    if len(ser_stat) == 1:
        if ser_stat[0].lower() in yes:
            return ["아니오", ser_stat[0]]
        elif ser_stat[0].lower() in no:
            return [ser_stat[0], "예"]
        else:
            found = False
    else:
        if ser_stat[0].lower() in yes:
            if ser_stat[1].lower() not in no:
                # print("중대하지 않은 '{}'을 [{}]에서 못 찾았어요".format(ser_stat[1], no))
                print("'{}'이 중대하지 않은 으로 진행합니다.".format(ser_stat[1]))
                confirm = input("확인? (y/n): ")
                while confirm != "n" and confirm != "y":
                    confirm = input("확인? (y/n): ")
                if confirm == "n":
                    return [ser_stat[0], ser_stat[1]]
            return [ser_stat[1], ser_stat[0]]
        elif ser_stat[0].lower() in no:
            if ser_stat[1].lower() not in yes:
                # print("중대한 '{}'을 [{}]에서 못 찾았어요".format(ser_stat[1], yes))
                print("'{}'이 중대한 으로 진행합니다.".format(ser_stat[1]))
                confirm = input("확인? (y/n): ")
                while confirm != "n" and confirm != "y":
                    confirm = input("확인? (y/n): ")
                    
                if confirm == "n":
                    return [ser_stat[1], ser_stat[0]]
            return [ser_stat[0], ser_stat[1]]
        else:
            found = False

    if not found:
        print("'중대성' column에서 '예', '아니오'을 찾지 못했습니다:")
        print("현재 중대성 column:")
        print(ser_stat)
        print("직접 선택하세요")
        truth = input("'{}'이 '중대한' 맞을까요? (혹은 '{}'이 중대하지 않은). Type y/n ".format(ser_stat[0], ser_stat[1]))
        if truth:
            return [ser_stat[1], ser_stat[0]]
        return [ser_stat[0], ser_stat[1]]
    
def ensure_order(table):
    '''Fixes minor bug on ordering trivial columns (e.g., 수집원, 이상사례종류, 허가사항반영여부)'''
    weightings = {"이상사례종류": 0, "중대한": 1, "중대하지 않은": 2, "허가사항반영여부": 3, "수집원": 4}

    ordered_tuple = list(table.columns)
    ordered_tuple.sort(key=lambda triple: weightings[triple[0]])
    
    ordered_col = pd.MultiIndex.from_tuples(ordered_tuple, names=table.columns.names)
    
    return pd.DataFrame(table, columns=ordered_col)

def finalize_columns(combined_in, adr, non_adr, serious, non_serious):
    ''' Updates column names and removes unnecessary'''
    warnings.simplefilter(action='ignore', category=pd.errors.PerformanceWarning)
    combined_in = combined_in.drop(columns=["SOC", "stat", "SOC#PT", "자료원"]) 
    
    pairing_0 = {'PT':'이상사례종류',
                 non_serious:'중대하지 않은',
                 serious:'중대한',
                 'Expectedness':'허가사항반영여부'}

    pairing_2 = {non_adr : "이상사례, 건",
                 adr : "약물이상반응, 건"}
    
    combined_in = edit_multilevel_columns(combined_in, pairing_0, level=0)
    combined_in = edit_multilevel_columns(combined_in, pairing_2, level=2)
    
    return ensure_order(combined_in)


def add_missing_columns(table_in, seriousness, time, adr_status):
    table = table_in.copy()
    
    for s in seriousness:
        for t in time:
            for a in adr_status:

                found = False
                for row in table:
                    # print(row)
                    if s in row and t in row and a in row:
                        found = True
                        # print("Found")

                if not found:
                    # print(s, t, a, "combination not found")
                    table[s, t, a] = 0
                    
    return table.sort_index(axis=1, level=["중대성", "차수", "ADR 여부"], ascending=[False, True, False])


def transform_format(data_processed_in, mode=0):
    '''
    mode = 0 : SOC and PT 합치 된 포맷 (합계 포함)
    mode = 1 : SOC and PT 분리 된 포맷 (default)
    '''
    data_processed_in = data_processed_in.copy()
    
    data_processed_in = data_processed_in.sort_values(["SOC", "PT"])
    
    table = data_processed_in.groupby(["SOC", "PT", "ADR 여부",
                        "차수", "중대성", "자료원"]).count().unstack(level=-2,
                                                             fill_value=0).unstack(level=-2,
                                                                                   fill_value=0).unstack(level=-2,
                                                                                                         fill_value=0).sort_index(axis=1,
                                                                                                                                  level=["중대성", "차수", "ADR 여부"], ascending=[False, True, False])["Expectedness"]
    
    


    
    adr_status = identify_adrness(data_processed_in)
    # print("In {} ADR: '{}' NON-ADR: '{}'".format(adr_status, adr_status[1], adr_status[0]))
    seriousness = identify_seriousness(data_processed_in)
    time = pd.unique(data_processed_in["차수"])
    
    # All the ADR identification processing was necessary from having to know WHICH column was missing to add the proper one. No need anymore if we find a 
    # rigorous method to identify all missing columns and instantiate it with 0
    
    table = add_missing_columns(table, seriousness, time, adr_status)
    
    # Since non-ADR (i.e., AE) includes ADR events too. Add ADR events to non-ADR events 
    for s in seriousness:
        for t in time:
            table[s, t, adr_status[0]] = np.array(table[s, t, adr_status[0]]) + np.array(table[s, t, adr_status[1]])
    
    
    # Add expectedness column
    table_df = table.reset_index()
    table_df['SOC#PT'] = table_df['SOC'] + '#' + table_df['PT']
    e_key = make_expectedness_key(data_processed_in)
    table["Expectedness"] = e_key[table_df["SOC#PT"]].values[0]        
    table["수집원"] = list(table.reset_index()["자료원"])
    table = table.droplevel("자료원")
    
    if mode == 1:
        return table
    
    # Merge PT and SOC into one column
    table_df = table.reset_index()
    table_df['SOC#PT'] = table_df['SOC'] + '#' + table_df['PT']
    table_df["stat"] = 1
    # supress performance warnings
    warnings.simplefilter(action='ignore', category=pd.errors.PerformanceWarning)
    sum_stat = table_df.groupby("SOC").sum()
    sum_stat["Expectedness"] = "" 
    sum_stat["자료원"] = ""
    sum_stat["stat"] = 0
    sum_stat = sum_stat.reset_index()
    sum_stat["PT"] = sum_stat["SOC"]
        
    combined = pd.concat([table_df, sum_stat]).reset_index(drop=True)
    combined = combined.sort_values(["SOC", "stat"]).reset_index(drop=True) 
    combined["수집원"] = combined["수집원"].fillna("")
    
    return finalize_columns(combined, adr_status[1], adr_status[0], seriousness[1], seriousness[0])
    
    

def control_process(uploader, main_display, option=0):
    pd.options.mode.chained_assignment = None 
    
    if option == 0:
        print("Note: 일람표 포맷 선택 되었습니다. 포맷 변경은 option=1로 가능합니다.")
    
    if main_display:
        print("File submitted...")
        data = load_from_widget(uploader)
        data_cleaned = auto_cleaner(data)
        data_binary = process_binary(data_cleaned)
        data_meddra = process_meddra(data_binary) 
        data_processed = process_time(data_meddra)
        final = transform_format(data_processed, option)
        return final
    else:
        print("File not recognized")