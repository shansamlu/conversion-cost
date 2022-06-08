import pandas as pd
import sys
from os import listdir
import numpy as np


def print_hi(name):
    print(f'Hi, {name}')


def load_wear_off():
    input_dir = r"C:\Users\mm13825\OneDrive - MassMutual\MyDocuments\Life\2022 Summer Intern\Data.xlsx"
    xl = pd.ExcelFile(input_dir)
    df = xl.parse(sheet_name='Wear-Off', skiprows=1)
    df = df.fillna(100)
    df = df.iloc[:, 1:]
    return np.array(df)


def load_mortality_risk_class_factors():
    input_dir = r"C:\Users\mm13825\OneDrive - MassMutual\MyDocuments\Life\2022 Summer Intern\Data.xlsx"
    xl = pd.ExcelFile(input_dir)
    df = xl.parse(sheet_name='Mortality Risk Class Factors', skiprows=1)
    df = df.iloc[:, 1:]
    return np.array(df)


def load_mm21():
    input_dir = r"C:\Users\mm13825\OneDrive - MassMutual\MyDocuments\Life\2022 Summer Intern\Data.xlsx"
    xl = pd.ExcelFile(input_dir)
    df = xl.parse(sheet_name='MM21', skiprows=0)
    # df = df.fillna(100)
    df = df.set_index('Key')
    df = df.iloc[:, 3:]
    return df


def load_anti_selection_factors():
    input_dir = r"C:\Users\mm13825\OneDrive - MassMutual\MyDocuments\Life\2022 Summer Intern\Data.xlsx"
    xl = pd.ExcelFile(input_dir)
    df = xl.parse(sheet_name='Anti Selection Factors', skiprows=1)
    return df


def load_2017_cso_ult():
    input_dir = r"C:\Users\mm13825\OneDrive - MassMutual\MyDocuments\Life\2022 Summer Intern\Data.xlsx"
    xl = pd.ExcelFile(input_dir)
    df = xl.parse(sheet_name='2017 CSO Ult', skiprows=1)
    return df


WEAR_OFF = load_wear_off()
MORTALITY_RISK_CLASS_FACTORS = load_mortality_risk_class_factors()
MM21 = load_mm21()
ANTI_SELECTION_FACTORS = load_mortality_risk_class_factors()
CSO_2017 = load_2017_cso_ult()

def get_risk_class_with_wear_off(issue_age, risk_class, sex):
    COLLUMN_DIC = {'UP': 0, 'SP': 1, 'NT': 2, 'ST': 3, 'T': 4, 'NC': 5, 'TC': 6}
    ROW_DIC = {"Male": 0, "Female": 1, "Ultimate": 2, "Smoker/Nonsmoker": 3}

    risk_class_factor = MORTALITY_RISK_CLASS_FACTORS[ROW_DIC[sex], COLLUMN_DIC[risk_class]]
    output = (1 - WEAR_OFF[issue_age] / 100) * risk_class_factor + WEAR_OFF[issue_age] / 100
    return output


def get_smoker(risk_class):
    SMOKER_DIC = {'UP': 'NS', 'SP': 'NS', 'NT': 'NS', 'ST': 'SM', 'T': 'SM', 'NC': 'NS', 'TC': 'SM'}
    return SMOKER_DIC[risk_class]


def get_underwritten_at_issue_mortality_version1(issue_age, risk_class, sex, mortality_improvement, mortality_improvement_years, is_mortality_improvement):
    smoker = get_smoker(risk_class)
    key = sex + smoker + str(issue_age)
    mm19_list = []
    improve_list = []
    for policy_year in range(1, 103):
        issue_year = issue_age + policy_year - 1
        if issue_year > 124:
            mm19 = 1000
        elif policy_year <= 26:
            mm19 = MM21.loc[key][policy_year]
        else:
            mm19 = MM21.loc[sex + smoker + str(issue_year - 25)][26]

        mm19_list.append(mm19)
    mm19_array = np.array(mm19_list)

    gqf_array = get_risk_class_with_wear_off(issue_age, risk_class, sex)[:102]

    for policy_year in range(1, 103):
        improve_list.append(pow((1-mortality_improvement), (min(policy_year,mortality_improvement_years))))

    improve_array = np.array(improve_list)

    if not is_mortality_improvement:
        improve_array = np.ones(102)

    q_array = mm19_array * gqf_array * improve_array

    policy_year_array = np.array(range(1, 103))
    issue_year_array = np.array(range(issue_age, issue_age+102))
    output_array = np.array([policy_year_array, issue_year_array, mm19_array, gqf_array, improve_array, q_array]).T
    return output_array


def get_underwritten_at_conversion_mortality_version1(issue_age, conversion_year, risk_class, sex, mortality_improvement, mortality_improvement_years, is_mortality_improvement):
    smoker = get_smoker(risk_class)
    attained_age = issue_age + conversion_year
    key = sex + smoker + str(attained_age)
    mm19_list = []
    improve_list = []
    for year_from_conversion in range(1, 103):
        attained_year = attained_age + year_from_conversion - 1
        if attained_year > 124:
            mm19 = 1000
        elif year_from_conversion <= 26:
            mm19 = MM21.loc[key][year_from_conversion]
        else:
            mm19 = MM21.loc[sex + smoker + str(attained_year - 25)][26]

        mm19_list.append(mm19)
    mm19_array = np.array(mm19_list)

    gqf_array = get_risk_class_with_wear_off(attained_age, risk_class, sex)[:102]

    for year_from_conversion in range(1, 103):
        improve_list.append(pow((1-mortality_improvement), (min(year_from_conversion + conversion_year, mortality_improvement_years))))

    improve_array = np.array(improve_list)

    if not is_mortality_improvement:
        improve_array = np.ones(102)

    q_array = mm19_array * gqf_array * improve_array

    year_from_conversion_array = np.array(range(1, 103))
    attained_year_array = np.array(range(attained_age, attained_age+102))
    output_array = np.array([year_from_conversion_array, attained_year_array, mm19_array, gqf_array, improve_array, q_array]).T
    return output_array


def get_underwritten_at_issue_mortality_version2(issue_age, smoker, sex, mortality_improvement, mortality_improvement_years):
    key_begin = sex + smoker + str(issue_age)
    key_end = set + smoker + '99'
    row_loc_begin = MM21.index.get_loc(key_begin)
    row_loc_end = MM21.index.get_loc(key_end)

    part_1 = MM21.iloc[row_loc_begin, :]
    part_2 = MM21.iloc[25, row_loc_begin + 1:row_loc_end]
    np.array(part_1)
    np.array(part_2)

    # for policy_year in range(1,102):
    #
    #     if issue_age > 124:
    #         MM19 = 1000
    #     elif policy_year <= 26:
    #         MM19 = MM21[MM21['Key'] == key][policy_year]
    #     else:
    #         MM19 = MM21



# def get_naar(sex, risk_class, age_to_endow, attained_age, interest_rate):
#     L100_INTEREST_RATE = 0.00375
#     L65_INTEREST_RATE = 0.003
#     L20_INTEREST_RATE = 0.003
#     L10_INTEREST_RATE = 0.002
#
#     cso_sex_risk_class = sex[0] + risk_class
#
#     for
#
#
#     for policy_year in range(1, age_to_endow - attained_age + 1):
#         attained_year = attained_age + policy_year - 1
#         if attained_year >= 100:
#             yearly_cso = 1
#         else:
#             yearly_cso = CSO_2017.loc[attained_year][cso_sex_risk_class]
#             monthly_cso = yearly_cso/12





if __name__ == '__main__':
    # output = get_risk_class_with_wear_off(40, 'NT', 'Female')
    # get_underwritten_at_issue_mortality_version1(45, 'NT', 'Female', 0.005, 10, True)
    get_underwritten_at_conversion_mortality_version1(45, 20, 'NT', 'Female', 0.005, 10, True)
