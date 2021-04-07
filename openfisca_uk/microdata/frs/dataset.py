import numpy as np
import pandas as pd
from family_resources_survey import FRS
from pathlib import Path
import shutil

DATA_STORE = Path(__file__).parent


class FRSDataset:
    def __init__(self, year: int):
        year = str(year)
        dataset_path = DATA_STORE / year
        if dataset_path.exists():
            person = pd.read_csv(dataset_path / "person.csv")
            benunit = pd.read_csv(dataset_path / "benunit.csv")
            household = pd.read_csv(dataset_path / "household.csv")
            self.entity_dfs = person, benunit, household
        else:
            self.entity_dfs = self.generate_dataset(year)

    def generate_dataset(self, year: int) -> None:
        """Generates a new FRS dataset.

        Args:
            year (int): The year of the FRS to use.

        Returns:
            Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]: The person, benefit unit and household datasets.
        """
        frs = FRS(year)

        # generate the person-level dataset

        person = frs.adult

        get_new_columns = lambda df: list(
            df.columns.difference(person.columns)
        ) + ["person_id"]
        person = pd.merge(
            frs.adult,
            frs.child[get_new_columns(frs.child)],
            how="outer",
            on="person_id",
        )

        # link capital income sources (amounts summed by account type)

        accounts = (
            frs.accounts[get_new_columns(frs.accounts)]
            .groupby(["person_id", "ACCOUNT"])
            .sum()
            .reset_index()
        )
        accounts = accounts.pivot(index="person_id", columns="ACCOUNT")[
            ["ACCINT"]
        ].reset_index()
        accounts.columns = accounts.columns.get_level_values(1)
        accounts = accounts.add_prefix("ACCINT_ACCOUNT_CODE_").reset_index()
        person = pd.merge(
            person,
            accounts,
            how="outer",
            left_on="person_id",
            right_on="ACCINT_ACCOUNT_CODE_",
        )

        # link benefit income sources (amounts summed by benefit program)

        bens = frs.benefits[get_new_columns(frs.benefits)]

        # distinguish income-related JSA and ESA from contribution-based variants
        
        bonus_to_IB_benefits = 1000 * (bens.VAR2.isin((2, 4)) * bens.BENEFIT.isin((14, 16)))
        bens["BENEFIT"] += bonus_to_IB_benefits
        benefits = (
            bens
            .groupby(["person_id", "BENEFIT"])
            .sum()
            .reset_index()
        )
        benefits = benefits.pivot(index="person_id", columns="BENEFIT")[
            ["BENAMT"]
        ].reset_index()
        benefits.columns = benefits.columns.get_level_values(1)
        benefits = benefits.add_prefix("BENAMT_BENEFIT_CODE_").reset_index()
        person = pd.merge(
            person,
            benefits,
            how="outer",
            left_on="person_id",
            right_on="BENAMT_BENEFIT_CODE_",
        )

        # link job-level data (all fields summed across all jobs)

        job = (
            frs.job[get_new_columns(frs.job)]
            .groupby("person_id")
            .sum()
            .reset_index()
        )
        person = pd.merge(person, job, how="outer", on="person_id").fillna(0)

        person["role"] = np.where(person.AGE80 >= 18, "adult", "child")
        person["benunit_id"] = person["person_id"] // 1e+1
        person["household_id"] = person["person_id"] // 1e+2
        person = person.add_prefix("P_")
        # generate benefit unit and household datasets

        benunit = frs.benunit.fillna(0).add_prefix("B_")
        household = frs.househol.fillna(0).add_prefix("H_")

        # store dataset for future use

        dataset_path = DATA_STORE / year

        if dataset_path.exists():
            shutil.rmtree(dataset_path)

        dataset_path.mkdir()
        person.to_csv(dataset_path / "person.csv", index=False)
        benunit.to_csv(dataset_path / "benunit.csv", index=False)
        household.to_csv(dataset_path / "household.csv", index=False)

        return person, benunit, household
