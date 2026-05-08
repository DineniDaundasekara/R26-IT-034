import joblib
import json
import os

def explain_decision(model_path, feature_names_path, sample_features):
    if not os.path.exists(model_path):
        return {
            "trust_score": 0,
            "risk_category": "Unknown",
            "explanations": ["Model not trained yet. Run ml_pipeline.py first."]
        }
    
    clf = joblib.load(model_path)
    with open(feature_names_path, "r") as f:
        feature_names = json.load(f)
        
    probs = clf.predict_proba([sample_features])[0]
    predicted_class = clf.predict([sample_features])[0]
    
    class_idx = list(clf.classes_).index("Low Risk") if "Low Risk" in clf.classes_ else 0
    trust_score = round(probs[class_idx] * 100)
    
    # Path extraction for XAI string array natively via DecisionTree
    node_indicator = clf.decision_path([sample_features])
    leaf_id = clf.apply([sample_features])[0]
    
    feature = clf.tree_.feature
    threshold = clf.tree_.threshold
    node_index = node_indicator.indices[node_indicator.indptr[0]:node_indicator.indptr[1]]
    
    explanations = []
    for node_id in node_index:
        if leaf_id == node_id:
            continue
            
        is_less_than = sample_features[feature[node_id]] <= threshold[node_id]
        sign = "<=" if is_less_than else ">"
        actual_val = sample_features[feature[node_id]]
        thresh_val = threshold[node_id]
        feature_name = feature_names[feature[node_id]]
        
        # Translate to human readable rule
        rule_str = translate_rule_to_hr_string(feature_name, sign, thresh_val, actual_val)
        explanations.append(rule_str)
        
    return {
        "trust_score": trust_score,
        "risk_category": predicted_class,
        "explanations": explanations if explanations else ["Direct rule logic matched."]
    }

def translate_rule_to_hr_string(feat, sign, thresh, actual):
    if feat == "github_public_repos":
        if sign == ">": return f"Strong open-source engagement (Repos = {actual} > {thresh:.1f})."
        else: return f"Limited public repository history (Repos = {actual} <= {thresh:.1f})."
    elif feat == "years_of_experience":
        if sign == ">": return f"Extensive professional experience (Years = {actual} > {thresh:.1f})."
        else: return f"Junior level professional experience (Years = {actual} <= {thresh:.1f})."
    elif feat == "skill_match_count":
        if sign == ">": return f"High alignment with required skills (Matched = {actual} > {thresh:.1f})."
        else: return f"Missing several core required skills (Matched = {actual} <= {thresh:.1f})."
    elif feat == "github_followers":
        if sign == ">": return f"Recognized in developer community (Followers = {actual} > {thresh:.1f})."
        else: return f"Standard community presence (Followers = {actual} <= {thresh:.1f})."
    elif feat == "commit_frequency":
        if sign == ">": return f"High coding activity and consistency (Frequency = {actual:.1f} > {thresh:.1f})."
        else: return f"Intermittent coding activity (Frequency = {actual:.1f} <= {thresh:.1f})."
    elif feat == "repo_quality_score":
        if sign == ">": return f"High-quality repositories with community engagement (Quality = {actual:.1f} > {thresh:.1f})."
        else: return f"Standard quality public projects (Quality = {actual:.1f} <= {thresh:.1f})."
    elif feat == "collaboration_score":
        if sign == ">": return f"Active collaborator in community projects (Collaboration = {actual:.1f} > {thresh:.1f})."
        else: return f"Primarily focused on independent projects (Collaboration = {actual:.1f} <= {thresh:.1f})."
    elif feat == "open_source_contributions":
        if sign == ">": return f"Significant contributions to open-source (OS Score = {actual:.1f} > {thresh:.1f})."
        else: return f"Limited external open-source footprint (OS Score = {actual:.1f} <= {thresh:.1f})."
    return f"{feat} {sign} {thresh} (Actual: {actual})"
