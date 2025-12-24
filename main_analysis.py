import logging
import os
import pickle
from pathlib import Path
from typing import Dict, Any
from logger_config import configure_logging
from participant_data import *
from questionnaire_loader import load_questionnaire_data
from visualizations import *
import pandas as pd
from scipy.stats import spearmanr
from sklearn.tree import DecisionTreeClassifier, export_text, plot_tree
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
import matplotlib.pyplot as plt
import seaborn as sns
from collections import defaultdict
from scipy.stats import kruskal
import scikit_posthocs as sp
from matplotlib.patches import Patch

def compute_questionnaire_descriptive_stats(questionnaire_df: pd.DataFrame):
    """
    Computes descriptive statistics (mean, std, median, min, max, count) for all numerical columns in the questionnaire.
    Saves the result as a CSV.
    """
    # Ensure numeric columns only
    numeric_df = questionnaire_df.select_dtypes(include='number')
    
    # Compute descriptive statistics
    stats_df = numeric_df.agg(['mean', 'std', 'median', 'min', 'max']).T.round(2)
    stats_df.index.name = "Question"

    # Save
    stats_df.to_csv("Questionnaire_Descriptive_Stats.csv", index=True)
    print(f"✅ Descriptive statistics saved")

    return stats_df

def collect_all_ratings(participants):
    data = []
    for participant in participants.values():
        pid = int(participant.participant_id)
        tour_type = participant.tour_type
        questionnaire = participant.questionnaire_data_unranked

        if questionnaire is None:
            continue

        for painting in ["Klimt", "Pollock", "van Dongen", "Braque", "de Chirico", "Janco", "Picasso"]:
            rating = questionnaire.get(painting)
            if pd.notna(rating):
                data.append({
                    "ParticipantID": pid,
                    "TourType": tour_type,
                    "Rating": int(rating)
                })

    return pd.DataFrame(data)

def plot_rating_distribution(df):
    # Map rating numbers to descriptive labels
    rating_labels = {
        1: "Did not like at all", 
        2: "Did not like", 
        3: "Quite disliked", 
        4: "Neutral",
        5: "Quite liked", 
        6: "Liked", 
        7: "Really liked"
    }
    df["RatingLabel"] = df["Rating"].map(rating_labels)

    # Define order of labels for plotting
    ordered_labels = list(rating_labels.values())

    # Compute average rating per tour type
    avg_by_type = df.groupby("TourType")["Rating"].mean().round(2).to_dict()

    # Compute proportions
    counts = df.groupby(["TourType", "RatingLabel"]).size().reset_index(name="Count")
    total_per_type = df["TourType"].value_counts().to_dict()
    counts["Proportion"] = counts.apply(
        lambda row: row["Count"] / total_per_type[row["TourType"]], axis=1
    )

    # Define consistent custom colors for the 3 tour types
    custom_palette = {
        1: "#3C3C3C",   # Dark gray
        2: "#B76E79",   # Dusty pink
        3: "#D9C8B4"    # Light beige
    }

    # Plot
    plt.figure(figsize=(14, 8))
    sns.barplot(
        data=counts,
        x="RatingLabel",
        y="Proportion",
        hue="TourType",
        palette=custom_palette,
        order=ordered_labels   # 👈 Force correct order here
    )

    legend_patches = [
        Patch(
            color=custom_palette[t], 
            label=f"{t} {'Fully active' if t==1 else 'Semi-active' if t==2 else 'Passive'} (Avg: {avg_by_type[t]})"
        )
        for t in sorted(avg_by_type.keys())
    ]
    plt.legend(title="Type", handles=legend_patches)

    plt.title("How much you liked all the paintings from the museum by Type")
    plt.xlabel("Rating")
    plt.ylabel("Proportion")
    plt.xticks(rotation=45)
    plt.ylim(0, 0.3)
    plt.tight_layout()
    plt.savefig("Average Liking by Type.png")
    plt.show() 

def run_total_time_vs_questionnaire_spearman(
    per_Participant_Summary: pd.DataFrame,
    questionnaire_df: pd.DataFrame,
    time_col: str = "TotalExperimentTime",
):

    # --- Normalize IDs/dtypes for a clean merge ---
    pps = per_Participant_Summary.copy()
    pps["ParticipantID"] = pd.to_numeric(pps["ParticipantID"], errors="coerce").astype("Int64")
    pps = pps[pps["ParticipantID"].notna()].copy()

    if time_col not in pps.columns:
        raise KeyError(f"'{time_col}' not found in per_Participant_Summary.")
    if "TourType" not in pps.columns:
        raise KeyError("'TourType' not found in per_Participant_Summary.")

    work_q = questionnaire_df.copy()
    work_q.index = pd.to_numeric(work_q.index, errors="coerce").astype("Int64")
    work_q = work_q[work_q.index.notna()].copy()

    # Fixed positional slice: columns 2:16 (3rd..16th columns)
    start, end = 0, 14
    if work_q.shape[1] <= start:
        raise ValueError(f"Questionnaire has only {work_q.shape[1]} columns; cannot select columns {start}:{end}.")
    q_slice = work_q.iloc[:, start:end].copy()

    # Coerce to numeric (Likert strings -> numbers if already encoded, else NaN)
    q_numeric = q_slice.apply(pd.to_numeric, errors="coerce")
    if q_numeric.empty:
        raise ValueError("Selected questionnaire columns (2:16) contain no numeric data after coercion.")

    # Merge time + type with questionnaire by ParticipantID
    base = pps[["ParticipantID", "TourType", time_col]].merge(
        q_numeric, left_on="ParticipantID", right_index=True, how="left"
    )

    # Actual types present
    type_values = sorted(base["TourType"].dropna().unique())

    rows = []

    def corr_row(frame: pd.DataFrame, question_col: str, label) -> dict:
        sub = frame[[time_col, question_col]].dropna()
        n = len(sub)
        if n >= 3 and sub[time_col].nunique() > 1 and sub[question_col].nunique() > 1:
            rho, p = spearmanr(sub[time_col], sub[question_col])
            return {"Question": question_col, "TourType": label,
                    "SpearmanRho": round(float(rho), 3),
                    "p-value": round(float(p), 4),
                    "N": int(n)}
        else:
            return {"Question": question_col, "TourType": label,
                    "SpearmanRho": None, "p-value": None, "N": int(n)}

    # For each question: ALL + per-type
    for col in q_numeric.columns:
        rows.append(corr_row(base, col, "All"))
        for t in type_values:
            rows.append(corr_row(base.loc[base["TourType"] == t], col, t))

    out = pd.DataFrame(rows).sort_values(["p-value", "Question"], na_position="last")
    out.to_csv("TotalExperimentTime_vs_Questionnaire_Spearman_by_Type.csv", index=False)
    print(out)
    return out
    
def run_tiletime_vs_questionnaire_spearman(per_Painting_Summary: pd.DataFrame,
                                           questionnaire: pd.DataFrame) -> pd.DataFrame:
    pps = per_Painting_Summary.copy()
    pps["ParticipantID"] = pd.to_numeric(pps["ParticipantID"], errors="coerce").astype("Int64")
    pps = pps[pps["ParticipantID"].notna()].copy()

    metrics = ["TimeAtTheTile", "TileTimePercent_Audio"]
    for m in metrics:
        if m not in pps.columns:
            raise KeyError(f"'{m}' not found in per_Painting_Summary.")

    q = questionnaire.copy().drop(columns=["Unnamed: 0"], errors="ignore")
    # use ParticipantID as the join key
    if "ParticipantID" in q.columns:
        q = q.set_index("ParticipantID", drop=False)
    q.index = pd.to_numeric(q.index, errors="coerce").astype("Int64")
    q = q[q.index.notna()].copy()

    # normalize type column name
    if "Type" not in q.columns and "TourType" in q.columns:
        q = q.rename(columns={"TourType": "Type"})
    if "Type" not in q.columns:
        raise KeyError("Questionnaire must contain 'Type' (or 'TourType').")

    # slice 2:16, drop Type from the slice, coerce numeric
    q_slice = q.iloc[:, 2:16].drop(columns=["Type"], errors="ignore").apply(pd.to_numeric, errors="coerce")
    # keep Type alongside
    q_join = pd.concat([q[["Type"]].astype("Int64"), q_slice], axis=1)

    merged = pps.merge(q_join, left_on="ParticipantID", right_index=True, how="left")
    type_values = sorted(merged["Type"].dropna().unique())

    def corr_row(frame: pd.DataFrame, metric: str, question: str, label):
        sub = frame[[metric, question]].dropna()
        if len(sub) >= 3 and sub[metric].nunique() > 1 and sub[question].nunique() > 1:
            rho, p = spearmanr(sub[metric], sub[question])
            return {"Metric": metric, "Question": question, "Type": label,
                    "SpearmanRho": round(float(rho), 3), "p-value": round(float(p), 4), "N": int(len(sub))}
        return {"Metric": metric, "Question": question, "Type": label,
                "SpearmanRho": None, "p-value": None, "N": int(len(sub))}

    rows = []
    for m in metrics:
        for qcol in q_slice.columns:
            rows.append(corr_row(merged, m, qcol, "All"))
            for t in type_values:
                rows.append(corr_row(merged.loc[merged["Type"] == t], m, qcol, t))

    out = pd.DataFrame(rows).sort_values(["p-value", "Metric", "Question"], na_position="last")
    out.to_csv("TileTime_vs_Questionnaire_Spearman_byType.csv", index=False)
    return out

def run_time_vs_gaze_spearman(
    df: pd.DataFrame,
    time_col: str = "TimeAtTheTile",
    gaze_col: str = "GazeTime",
    group_by: str | None = "Type",
):
    # safety checks
    for c in (time_col, gaze_col):
        if c not in df.columns:
            raise KeyError(f"Column '{c}' not found in dataframe.")

    def one_corr(block: pd.DataFrame, label: str) -> dict:
        sub = block[[time_col, gaze_col]].dropna()
        n = len(sub)
        if n >= 3 and sub[time_col].nunique() > 1 and sub[gaze_col].nunique() > 1:
            rho, p = spearmanr(sub[time_col], sub[gaze_col])
            return {"Group": label, "N": int(n),
                    "SpearmanRho": round(float(rho), 3),
                    "Spearman_p": round(float(p), 4)}
        else:
            return {"Group": label, "N": int(n),
                    "SpearmanRho": None, "Spearman_p": None}

    rows = [one_corr(df, "ALL")]

    if group_by and group_by in df.columns:
        for g, gdf in df.groupby(group_by):
            rows.append(one_corr(gdf, f"{group_by}={g}"))

    out = pd.DataFrame(rows)
    out.to_csv("Time_vs_Gaze_correlations_spearman.csv", index=False)
    print(out)
    return out
    
def add_type_column(questionnaire_df, participant_summary_df):
    df = questionnaire_df.copy()

    # --- 1) Extract IDs + TourType from the summary, regardless of where IDs live ---
    if "ParticipantID" in participant_summary_df.columns:
        sum_pid = participant_summary_df["ParticipantID"]
    else:
        # use the index as ParticipantID
        sum_pid = participant_summary_df.index

    # Coerce both PID and TourType to nullable integers
    sum_pid_int = pd.to_numeric(pd.Series(sum_pid), errors="coerce").astype("Int64")
    tour_type_int = pd.to_numeric(
        participant_summary_df["TourType"], errors="coerce"
    ).astype("Int64")

    # Build a Series mapping ParticipantID -> TourType
    type_map = pd.Series(tour_type_int.values, index=sum_pid_int)

    # --- 2) Coerce questionnaire index to the same dtype ---
    q_idx_int = pd.to_numeric(pd.Series(df.index), errors="coerce").astype("Int64")

    # --- 3) Align and insert Type as first visible column (right after the index) ---
    type_aligned = type_map.reindex(q_idx_int)
    df.insert(0, "Type", type_aligned.astype("Int64"))

    # --- 4) Report any still-missing IDs for quick debugging ---
    missing = df.index[df["Type"].isna()].tolist()
    if missing:
        print("Missing Type for IDs:", missing[:50], "...")  # show up to 50

    return df

def analyze_liking_vs_preference(questionnaire: pd.DataFrame) -> pd.DataFrame:
    """
    Correlates how much participants liked each artwork with how often they preferred it over a new artwork.
    Calculates results overall and split by TourType.

    Returns:
        DataFrame with columns: Painting, TourType, SpearmanRho, p-value, N
    """

    # Define the mapping of paintings to liking column and preference column + which option they are
    painting_map = {
        "Klimt":       {"liking_col": "Klimt", "pref_col": "Preferred image",       "option": 1},
        "van Dongen":  {"liking_col": "van Dongen", "pref_col": "Preferred image.1",     "option": 2},
        "Braque":      {"liking_col": "Braque", "pref_col": "Preferred image.2",     "option": 1},
        "Pollock":     {"liking_col": "Pollock", "pref_col": "Preferred image.3", "option": 2},
        "de Chirico":  {"liking_col": "de Chirico", "pref_col": "Preferred image.4",     "option": 2},
        "Janco":       {"liking_col": "Janco", "pref_col": "Preferred image.5",     "option": 2},
        "Picasso":     {"liking_col": "Picasso", "pref_col": "Preferred image.6",     "option": 2},
    }
    df = questionnaire.copy()
    df["ParticipantID"] = df.index

    results = []

    for painting, config in painting_map.items():
        liking_col = config["liking_col"]
        pref_col = config["pref_col"]
        correct_option = str(config["option"])

        # Create binary preference: 1 if chosen, 0 if not
        df[f"{painting}_Preferred"] = (
            df[pref_col].astype(str) == correct_option
        ).astype(int)
        # Run correlation overall and by TourType
        for tour in ["All", 1, 2, 3]: 
            if tour == "All":
                subset = df
                label = "All"
            else:
                subset = df[df["Type"] == tour]
                label = f"Type type: {tour}"

            x = pd.to_numeric(subset[liking_col], errors="coerce")
            #print("x = ", x)
            if f"{painting}_Preferred" not in subset.columns:
                logging.info(f"{painting}_Preferred column not found. Skipping.")
                continue
            y = pd.to_numeric(subset[f"{painting}_Preferred"], errors="coerce")
            #print("y = ", y)

            valid = (~x.isna()) & (~y.isna())
            x, y = x[valid], y[valid]

            if len(x) > 2 and len(x.unique()) > 1 and len(y.unique()) > 1:
                rho, p = spearmanr(x, y)
                results.append({
                    "Painting": painting,
                    "Type": label,
                    "SpearmanRho": round(rho, 3),
                    "p-value": round(p, 4),
                    "N": len(x)
                })
    results = pd.DataFrame(results)
    results.to_csv("Liking_vs_Preference_by_Type.csv", index=False)
    print(results)
    return pd.DataFrame(results)

def analyze_preference_vs_measures(
    questionnaire_df: pd.DataFrame,
    per_Painting_Summary: pd.DataFrame,
) -> pd.DataFrame:
    """
    For each painting:
      1) Build a binary preference label from questionnaire (1 = preferred tour painting; 0 = preferred new).
      2) Merge that label onto painting-level rows by ParticipantID.
      3) For every numeric metric in per_Painting_Summary (except IDs), compute Spearman correlation with preference.
    Returns: DataFrame with columns [Painting, Metric, SpearmanRho, p-value, N]
    """

    painting_map = {
        "Klimt":       {"pref_col": "Preferred image",   "option": 1},
        "van Dongen":  {"pref_col": "Preferred image.1", "option": 2},
        "Braque":      {"pref_col": "Preferred image.2", "option": 1},
        "Pollock":     {"pref_col": "Preferred image.3", "option": 2},
        "de Chirico":  {"pref_col": "Preferred image.4", "option": 2},
        "Janco":       {"pref_col": "Preferred image.5", "option": 2},
        "Picasso":     {"pref_col": "Preferred image.6", "option": 2},
    }

    # --- Normalize IDs for a clean merge ---
    pps = per_Painting_Summary.copy()
    pps["ParticipantID"] = pd.to_numeric(pps["ParticipantID"], errors="coerce").astype("Int64")
    pps = pps[pps["ParticipantID"].notna()].copy()

    work = questionnaire_df.copy()
    work.index = pd.to_numeric(work.index, errors="coerce").astype("Int64")
    work = work[work.index.notna()].copy()

    # Detect painting name column
    if "Painting" in pps.columns:
        painting_col = "Painting"
    else:
        raise KeyError("per_Painting_Summary must contain 'Painting' or 'PaintingName'.")

    # Numeric metrics to test (exclude identifiers if present)
    metrics = pps.select_dtypes(include="number").columns.tolist()
    for col in ["ParticipantID", "TourType", "Painting"]:
        if col in metrics:
            metrics.remove(col)

    results = []

    for painting, cfg in painting_map.items():
        pref_col = cfg["pref_col"]
        correct_option = str(cfg["option"])
        yname = f"{pref_col}_PreferredTour"

        if pref_col not in work.columns:
            # Missing question column → skip this painting
            continue

        # 1) Binary preference per participant (index = ParticipantID)
        work[yname] = (work[pref_col].astype(str) == correct_option).astype(int)

        # 2) Painting rows for this painting, then merge preference by ParticipantID
        block = pps.loc[pps[painting_col] == painting].copy()
        if block.empty:
            continue

        merged = block.merge(
            work[[yname]],
            left_on="ParticipantID",
            right_index=True,
            how="left"
        )

        # 3) Correlate every numeric metric vs preference (overall only)
        for m in metrics:
            sub = merged[[m, yname]].dropna()
            n = len(sub)
            if n >= 3 and sub[m].nunique() > 1 and sub[yname].nunique() > 1:
                rho, p = spearmanr(sub[m], sub[yname])
                results.append({
                    "Painting": painting,
                    "Metric": m,
                    "SpearmanRho": round(float(rho), 3),
                    "p-value": round(float(p), 4),
                    "N": int(n),
                })
            else:
                results.append({
                    "Painting": painting,
                    "Metric": m,
                    "SpearmanRho": None,
                    "p-value": None,
                    "N": int(n),
                })

    out = pd.DataFrame(results).sort_values(["Painting", "p-value", "Metric"], na_position="last")
    out.to_csv("Preference_vs_Painting_Measures_Spearman.csv", index=False)
    print(out)
    return out

def analyze_vr_correlation_with_liking(per_Painting_Summary: pd.DataFrame, per_Participant_Summary: pd.DataFrame):
    # --- Painting-Level Analysis ---
    target = "SelfReportedLiking"
    numeric_cols_painting = per_Painting_Summary.select_dtypes(include='number').columns.tolist()
    numeric_cols_painting = [col for col in numeric_cols_painting if col != "ParticipantID"]
    subset_painting = per_Painting_Summary[numeric_cols_painting].dropna()

    correlations_painting = []
    for col in numeric_cols_painting:
        if col == target:
            continue
        rho, p = spearmanr(subset_painting[target], subset_painting[col])
        correlations_painting.append({
            "Feature": col,
            "SpearmanRho": round(rho, 3),
            "p_value": round(p, 4)
        })

    df_painting = pd.DataFrame(correlations_painting).sort_values(by="SpearmanRho", key=abs, ascending=False)
    df_painting.to_csv("correlation_of_VR_measures_with_liking_per_painting.csv", index=False)

    # --- Participant-Level Analysis ---
    target_2 = "Q1_SatisfactionTour"
    numeric_cols_participant = per_Participant_Summary.select_dtypes(include='number').columns.tolist()
    numeric_cols_participant = [col for col in numeric_cols_participant if col != "ParticipantID"]
    subset_participant = per_Participant_Summary[numeric_cols_participant].dropna()

    if target_2 not in subset_participant.columns:
        print(f"⚠️ '{target_2}' not found in per_Participant_Summary. Skipping participant-level analysis.")
        return

    correlations_participant = []
    for col in numeric_cols_participant:
        if col == target_2:
            continue
        rho, p = spearmanr(subset_participant[target_2], subset_participant[col])
        correlations_participant.append({
            "Feature": col,
            "SpearmanRho": round(rho, 3),
            "p_value": round(p, 4)
        })

    df_participant = pd.DataFrame(correlations_participant).sort_values(by="SpearmanRho", key=abs, ascending=False)
    df_participant.to_csv("correlation_of_VR_measures_with_liking_per_participant.csv", index=False)
    print("✅ Saved correlation results to both correlation_of_VR_measures_with_liking_per_painting.csv and _per_participant.csv")
    print(df_participant)

def run_questionnaire_anova(questionnaire):
     
    question_columns = questionnaire.columns[2:16]

    results = []
    for col in question_columns:
        groups = [questionnaire[questionnaire["Type"] == t][col].dropna() for t in [1, 2, 3]]
        stat, p = kruskal(*groups)
        results.append({
            "Question": col,
            "H-stat": round(stat, 3),
            "p-value": round(p, 4)
        })

    pd.DataFrame(results).to_csv("Questionnaire_Kruskal_by_Type.csv", index=False)
    print(pd.DataFrame(results))

def run_per_participant_kruskal(per_Participant_Summary: pd.DataFrame):
    # Get all numeric columns except TourType
    numeric_cols = per_Participant_Summary.select_dtypes(include="number").columns.tolist()
    if "TourType" in numeric_cols:
        numeric_cols.remove("TourType")

    # Group by TourType for descriptive stats
    grouped = per_Participant_Summary.groupby("TourType")[numeric_cols]
    grouped.agg(["mean", "std", "median", "min", "max", "count"]).round(2)\
        .to_csv("Participant_Level_Descriptive_Stats.csv")

    # Run Kruskal-Wallis for each numeric column
    results = []
    for metric in numeric_cols:
        groups = [
            per_Participant_Summary.loc[per_Participant_Summary["TourType"] == t, metric].dropna()
            for t in sorted(per_Participant_Summary["TourType"].unique())
        ]
        if all(len(g) > 0 for g in groups):  # only run if all groups have data
            stat, p = kruskal(*groups)
            results.append({"Metric": metric, "H-stat": round(stat, 3), "p-value": round(p, 4)})

    new = pd.DataFrame(results).sort_values("p-value")
    new.to_csv("Measures per participant across types, kruskal.csv", index=False)
    print(new)

def run_per_painting_kruskal(per_Painting_Summary: pd.DataFrame, per_Participant_Summary: pd.DataFrame):
    # Add TourType to the painting-level summary
    participant_df = per_Participant_Summary[["ParticipantID", "TourType"]]
    merged = per_Painting_Summary.merge(participant_df, on="ParticipantID")

    # Get all numeric columns except identifiers
    numeric_cols = merged.select_dtypes(include="number").columns.tolist()
    for col in ["ParticipantID", "TourType"]:
        if col in numeric_cols:
            numeric_cols.remove(col)

    # Group by TourType for descriptive stats
    grouped = merged.groupby("TourType")[numeric_cols]
    grouped.agg(["mean", "std", "median", "min", "max", "count"]).round(2)\
        .to_csv("Painting_Level_Descriptive_Stats.csv")

    # Run Kruskal-Wallis for each numeric column
    results = []
    for metric in numeric_cols:
        groups = [
            merged.loc[merged["TourType"] == t, metric].dropna()
            for t in sorted(merged["TourType"].unique())
        ]
        if all(len(g) > 0 for g in groups):  # only run if all groups have data
            stat, p = kruskal(*groups)
            results.append({"Metric": metric, "H-stat": round(stat, 3), "p-value": round(p, 4)})

    results_df = pd.DataFrame(results).sort_values("p-value")
    results_df.to_csv("Measures per painting across types, kruskal.csv", index=False)
    print(results_df)
    return merged

def run_per_painting_spearman(
    merged_df: pd.DataFrame,
    target_col: str = "SelfReportedLiking",
    extra_exclude: list[str] | None = None,
):
    # 1) Build the metric list dynamically from numeric columns
    numeric_cols = merged_df.select_dtypes(include="number").columns.tolist()

    # Columns to exclude from metrics (ids/grouping/target)
    exclude = {
        target_col,
        "TourType",
        "ParticipantID",
        "PaintingID",
    }
    # Sometimes names vary; safely drop if present
    exclude |= set(c for c in ["Painting", "PaintingName"] if c in merged_df.columns)
    if extra_exclude:
        exclude |= set(extra_exclude)

    metrics = [c for c in numeric_cols if c not in exclude]

    # 2) Iterate over real TourType values present
    type_values = sorted(merged_df["TourType"].dropna().unique())

    correlations = []
    for metric in metrics:
        for t in type_values:
            subset = merged_df.loc[merged_df["TourType"] == t, [metric, target_col]].dropna()

            # Need at least 3 points and variability in both vars
            if len(subset) >= 3 and subset[metric].nunique() > 1 and subset[target_col].nunique() > 1:
                rho, p = spearmanr(subset[metric], subset[target_col])
                correlations.append({
                    "Metric": metric,
                    "TourType": t,
                    "SpearmanRho": round(float(rho), 3),
                    "p-value": round(float(p), 4),
                    "N": int(len(subset)),
                })
            else:
                # Record as NA if not enough data / no variation
                correlations.append({
                    "Metric": metric,
                    "TourType": t,
                    "SpearmanRho": None,
                    "p-value": None,
                    "N": int(len(subset)),
                })

    out = pd.DataFrame(correlations).sort_values(["p-value", "Metric"], na_position="last")
    out.to_csv("Measures per painting across types, spearman.csv", index=False)
    print(out)
    return out
            

import pandas as pd
from scipy.stats import spearmanr

def run_per_participant_spearman(
    per_Participant_Summary: pd.DataFrame,
    target_col: str = "AvgGeneralRating",
    extra_exclude: list[str] | None = None,
):
    # 1) Collect numeric columns and drop identifiers/target
    numeric_cols = per_Participant_Summary.select_dtypes(include="number").columns.tolist()
    exclude = {"TourType", "ParticipantID", target_col}
    if extra_exclude:
        exclude |= set(extra_exclude)
    metrics = [c for c in numeric_cols if c not in exclude]

    # 2) Iterate over actual tour types present
    type_values = sorted(per_Participant_Summary["TourType"].dropna().unique())

    # 3) Spearman per metric × type
    rows = []
    for m in metrics:
        for t in type_values:
            sub = per_Participant_Summary.loc[
                per_Participant_Summary["TourType"] == t, [m, target_col]
            ].dropna()

            if len(sub) >= 3 and sub[m].nunique() > 1 and sub[target_col].nunique() > 1:
                rho, p = spearmanr(sub[m], sub[target_col])
                rows.append({
                    "Metric": m, "TourType": t,
                    "SpearmanRho": round(float(rho), 3),
                    "p-value": round(float(p), 4),
                    "N": int(len(sub)),
                })
            else:
                rows.append({
                    "Metric": m, "TourType": t,
                    "SpearmanRho": None, "p-value": None,
                    "N": int(len(sub)),
                })

    out = pd.DataFrame(rows).sort_values(["p-value", "Metric"], na_position="last")
    out.to_csv("Measures per participant across types, spearman.csv", index=False)
    print(out)
    return out

