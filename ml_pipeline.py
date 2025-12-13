"""
Smart Poultry Heater Control System - ML Pipeline
==================================================
This script performs:
1. Data exploration and visualization
2. Model training and comparison
3. Hyperparameter tuning
4. Model quantization for embedded deployment
5. Model export for microcontroller deployment
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split, GridSearchCV, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    confusion_matrix, classification_report, roc_auc_score, roc_curve
)
from sklearn.tree import export_text, plot_tree
import joblib
import json
import warnings
warnings.filterwarnings('ignore')

# Set style for better visualizations
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (12, 6)
plt.rcParams['font.size'] = 10

class PoultryHeaterMLPipeline:
    """Complete ML pipeline for poultry heater control system"""
    
    def __init__(self, data_path):
        self.data_path = data_path
        self.df = None
        self.X_train = None
        self.X_test = None
        self.y_train = None
        self.y_test = None
        self.scaler = StandardScaler()
        self.models = {}
        self.results = {}
        self.best_model = None
        self.best_model_name = None
        
    def load_data(self):
        """Load and display basic information about the dataset"""
        print("=" * 80)
        print("📊 LOADING DATA")
        print("=" * 80)
        
        self.df = pd.read_csv(self.data_path)
        print(f"\n✓ Dataset loaded successfully!")
        print(f"  Shape: {self.df.shape}")
        print(f"  Rows: {self.df.shape[0]:,}")
        print(f"  Columns: {self.df.shape[1]}")
        
        print("\n📋 First few rows:")
        print(self.df.head(10))
        
        print("\n📊 Dataset Info:")
        print(self.df.info())
        
        print("\n📈 Statistical Summary:")
        print(self.df.describe())
        
        return self.df
    
    def explore_data(self):
        """Comprehensive data exploration and visualization"""
        print("\n" + "=" * 80)
        print("🔍 DATA EXPLORATION")
        print("=" * 80)
        
        # Check for missing values
        print("\n🔎 Missing Values:")
        missing = self.df.isnull().sum()
        print(missing)
        if missing.sum() == 0:
            print("✓ No missing values found!")
        
        # Check for duplicates
        duplicates = self.df.duplicated().sum()
        print(f"\n🔎 Duplicate Rows: {duplicates}")
        
        # Class distribution
        print("\n🎯 Target Variable Distribution (Heater):")
        heater_dist = self.df['Heater'].value_counts()
        print(heater_dist)
        print(f"\nClass Balance:")
        print(f"  OFF (0): {heater_dist[0]:,} ({heater_dist[0]/len(self.df)*100:.2f}%)")
        print(f"  ON  (1): {heater_dist[1]:,} ({heater_dist[1]/len(self.df)*100:.2f}%)")
        
        # Feature ranges
        print("\n📏 Feature Ranges:")
        for col in ['Temp', 'Humidity', 'LDR']:
            print(f"  {col:10s}: [{self.df[col].min():.1f}, {self.df[col].max():.1f}]")
        
        # Correlation analysis
        print("\n🔗 Correlation Matrix:")
        corr_matrix = self.df.corr()
        print(corr_matrix)
        
        print("\n🎯 Correlation with Heater:")
        heater_corr = corr_matrix['Heater'].sort_values(ascending=False)
        print(heater_corr)
        
        # Create visualizations
        self._create_visualizations()
        
    def _create_visualizations(self):
        """Create comprehensive visualizations"""
        print("\n📊 Creating visualizations...")
        
        # 1. Distribution plots
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        fig.suptitle('Feature Distributions and Target Variable', fontsize=16, fontweight='bold')
        
        # Temperature distribution
        axes[0, 0].hist(self.df['Temp'], bins=30, color='#FF6B6B', alpha=0.7, edgecolor='black')
        axes[0, 0].set_title('Temperature Distribution', fontweight='bold')
        axes[0, 0].set_xlabel('Temperature (°C)')
        axes[0, 0].set_ylabel('Frequency')
        axes[0, 0].grid(True, alpha=0.3)
        
        # Humidity distribution
        axes[0, 1].hist(self.df['Humidity'], bins=30, color='#4ECDC4', alpha=0.7, edgecolor='black')
        axes[0, 1].set_title('Humidity Distribution', fontweight='bold')
        axes[0, 1].set_xlabel('Humidity (%)')
        axes[0, 1].set_ylabel('Frequency')
        axes[0, 1].grid(True, alpha=0.3)
        
        # LDR distribution
        axes[1, 0].hist(self.df['LDR'], bins=30, color='#FFE66D', alpha=0.7, edgecolor='black')
        axes[1, 0].set_title('Light Intensity (LDR) Distribution', fontweight='bold')
        axes[1, 0].set_xlabel('LDR Value (0-100)')
        axes[1, 0].set_ylabel('Frequency')
        axes[1, 0].grid(True, alpha=0.3)
        
        # Heater state distribution
        heater_counts = self.df['Heater'].value_counts()
        colors = ['#95E1D3', '#F38181']
        axes[1, 1].bar(['OFF (0)', 'ON (1)'], heater_counts.values, color=colors, alpha=0.7, edgecolor='black')
        axes[1, 1].set_title('Heater State Distribution', fontweight='bold')
        axes[1, 1].set_ylabel('Count')
        axes[1, 1].grid(True, alpha=0.3, axis='y')
        
        plt.tight_layout()
        plt.savefig('visualizations_distributions.png', dpi=300, bbox_inches='tight')
        print("  ✓ Saved: visualizations_distributions.png")
        plt.close()
        
        # 2. Correlation heatmap
        fig, ax = plt.subplots(figsize=(10, 8))
        sns.heatmap(self.df.corr(), annot=True, cmap='coolwarm', center=0, 
                    square=True, linewidths=1, cbar_kws={"shrink": 0.8}, ax=ax)
        ax.set_title('Feature Correlation Heatmap', fontsize=16, fontweight='bold', pad=20)
        plt.tight_layout()
        plt.savefig('visualizations_correlation.png', dpi=300, bbox_inches='tight')
        print("  ✓ Saved: visualizations_correlation.png")
        plt.close()
        
        # 3. Pairplot by heater state
        print("  ⏳ Creating pairplot (this may take a moment)...")
        sample_df = self.df.sample(n=min(5000, len(self.df)), random_state=42)
        g = sns.pairplot(sample_df, hue='Heater', palette={0: '#95E1D3', 1: '#F38181'}, 
                        diag_kind='kde', plot_kws={'alpha': 0.6})
        g.fig.suptitle('Feature Relationships by Heater State', y=1.02, fontsize=16, fontweight='bold')
        plt.savefig('visualizations_pairplot.png', dpi=300, bbox_inches='tight')
        print("  ✓ Saved: visualizations_pairplot.png")
        plt.close()
        
        # 4. Box plots by heater state
        fig, axes = plt.subplots(1, 3, figsize=(18, 5))
        fig.suptitle('Feature Distributions by Heater State', fontsize=16, fontweight='bold')
        
        features = ['Temp', 'Humidity', 'LDR']
        colors_box = ['#FF6B6B', '#4ECDC4', '#FFE66D']
        
        for idx, (feature, color) in enumerate(zip(features, colors_box)):
            sns.boxplot(data=self.df, x='Heater', y=feature, palette=['#95E1D3', '#F38181'], ax=axes[idx])
            axes[idx].set_title(f'{feature} by Heater State', fontweight='bold')
            axes[idx].set_xlabel('Heater State')
            axes[idx].set_xticklabels(['OFF (0)', 'ON (1)'])
            axes[idx].grid(True, alpha=0.3, axis='y')
        
        plt.tight_layout()
        plt.savefig('visualizations_boxplots.png', dpi=300, bbox_inches='tight')
        print("  ✓ Saved: visualizations_boxplots.png")
        plt.close()
        
        print("\n✓ All visualizations created successfully!")
    
    def prepare_data(self, test_size=0.2, random_state=42):
        """Prepare data for training"""
        print("\n" + "=" * 80)
        print("🔧 PREPARING DATA")
        print("=" * 80)
        
        # Separate features and target
        X = self.df[['Temp', 'Humidity', 'LDR']]
        y = self.df['Heater']
        
        # Split data
        self.X_train, self.X_test, self.y_train, self.y_test = train_test_split(
            X, y, test_size=test_size, random_state=random_state, stratify=y
        )
        
        print(f"\n✓ Data split completed:")
        print(f"  Training set: {len(self.X_train):,} samples ({len(self.X_train)/len(X)*100:.1f}%)")
        print(f"  Test set:     {len(self.X_test):,} samples ({len(self.X_test)/len(X)*100:.1f}%)")
        
        print(f"\n✓ Class distribution in training set:")
        train_dist = self.y_train.value_counts()
        print(f"  OFF (0): {train_dist[0]:,} ({train_dist[0]/len(self.y_train)*100:.2f}%)")
        print(f"  ON  (1): {train_dist[1]:,} ({train_dist[1]/len(self.y_train)*100:.2f}%)")
        
        # Note: We'll apply scaling per model as needed
        print("\n✓ Data preparation complete!")
        
    def train_models(self):
        """Train multiple models and compare performance"""
        print("\n" + "=" * 80)
        print("🤖 TRAINING MODELS")
        print("=" * 80)
        
        # Define models
        self.models = {
            'Logistic Regression': LogisticRegression(random_state=42, max_iter=1000),
            'Decision Tree': DecisionTreeClassifier(random_state=42, max_depth=10),
            'Random Forest': RandomForestClassifier(random_state=42, n_estimators=100, max_depth=10),
            'Gradient Boosting': GradientBoostingClassifier(random_state=42, n_estimators=100, max_depth=5)
        }
        
        # Train and evaluate each model
        for name, model in self.models.items():
            print(f"\n{'─' * 80}")
            print(f"🔄 Training: {name}")
            print(f"{'─' * 80}")
            
            # Scale data for models that benefit from it
            if name in ['Logistic Regression']:
                scaler = StandardScaler()
                X_train_scaled = scaler.fit_transform(self.X_train)
                X_test_scaled = scaler.transform(self.X_test)
                
                model.fit(X_train_scaled, self.y_train)
                y_pred = model.predict(X_test_scaled)
                y_pred_proba = model.predict_proba(X_test_scaled)[:, 1]
            else:
                model.fit(self.X_train, self.y_train)
                y_pred = model.predict(self.X_test)
                y_pred_proba = model.predict_proba(self.X_test)[:, 1]
            
            # Calculate metrics
            accuracy = accuracy_score(self.y_test, y_pred)
            precision = precision_score(self.y_test, y_pred)
            recall = recall_score(self.y_test, y_pred)
            f1 = f1_score(self.y_test, y_pred)
            roc_auc = roc_auc_score(self.y_test, y_pred_proba)
            
            # Cross-validation score
            if name in ['Logistic Regression']:
                cv_scores = cross_val_score(model, X_train_scaled, self.y_train, cv=5)
            else:
                cv_scores = cross_val_score(model, self.X_train, self.y_train, cv=5)
            
            # Store results
            self.results[name] = {
                'model': model,
                'accuracy': accuracy,
                'precision': precision,
                'recall': recall,
                'f1': f1,
                'roc_auc': roc_auc,
                'cv_mean': cv_scores.mean(),
                'cv_std': cv_scores.std(),
                'y_pred': y_pred,
                'y_pred_proba': y_pred_proba,
                'confusion_matrix': confusion_matrix(self.y_test, y_pred)
            }
            
            # Print results
            print(f"\n📊 Results:")
            print(f"  Accuracy:  {accuracy:.4f}")
            print(f"  Precision: {precision:.4f}")
            print(f"  Recall:    {recall:.4f}")
            print(f"  F1 Score:  {f1:.4f}")
            print(f"  ROC AUC:   {roc_auc:.4f}")
            print(f"  CV Score:  {cv_scores.mean():.4f} (+/- {cv_scores.std():.4f})")
            
            print(f"\n📋 Confusion Matrix:")
            print(self.results[name]['confusion_matrix'])
            
        # Determine best model
        self._select_best_model()
        self._create_model_comparison_plots()
        
    def _select_best_model(self):
        """Select the best performing model"""
        print("\n" + "=" * 80)
        print("🏆 MODEL COMPARISON")
        print("=" * 80)
        
        # Create comparison dataframe
        comparison_df = pd.DataFrame({
            'Model': list(self.results.keys()),
            'Accuracy': [r['accuracy'] for r in self.results.values()],
            'Precision': [r['precision'] for r in self.results.values()],
            'Recall': [r['recall'] for r in self.results.values()],
            'F1 Score': [r['f1'] for r in self.results.values()],
            'ROC AUC': [r['roc_auc'] for r in self.results.values()],
            'CV Mean': [r['cv_mean'] for r in self.results.values()]
        })
        
        comparison_df = comparison_df.sort_values('F1 Score', ascending=False)
        print("\n📊 Model Performance Comparison:")
        print(comparison_df.to_string(index=False))
        
        # Select best model based on F1 score (balanced metric)
        self.best_model_name = comparison_df.iloc[0]['Model']
        self.best_model = self.results[self.best_model_name]['model']
        
        print(f"\n🥇 Best Model: {self.best_model_name}")
        print(f"   F1 Score: {comparison_df.iloc[0]['F1 Score']:.4f}")
        
    def _create_model_comparison_plots(self):
        """Create visualizations comparing model performance"""
        print("\n📊 Creating model comparison visualizations...")
        
        # 1. Metrics comparison
        metrics = ['Accuracy', 'Precision', 'Recall', 'F1 Score', 'ROC AUC']
        model_names = list(self.results.keys())
        
        fig, ax = plt.subplots(figsize=(14, 8))
        x = np.arange(len(model_names))
        width = 0.15
        
        colors = ['#FF6B6B', '#4ECDC4', '#FFE66D', '#95E1D3', '#F38181']
        
        for idx, (metric, color) in enumerate(zip(metrics, colors)):
            metric_key = 'f1' if metric == 'F1 Score' else metric.lower().replace(' ', '_')
            values = [self.results[name][metric_key] for name in model_names]
            ax.bar(x + idx * width, values, width, label=metric, color=color, alpha=0.8, edgecolor='black')
        
        ax.set_xlabel('Models', fontweight='bold', fontsize=12)
        ax.set_ylabel('Score', fontweight='bold', fontsize=12)
        ax.set_title('Model Performance Comparison', fontweight='bold', fontsize=16, pad=20)
        ax.set_xticks(x + width * 2)
        ax.set_xticklabels(model_names, rotation=15, ha='right')
        ax.legend(loc='lower right')
        ax.grid(True, alpha=0.3, axis='y')
        ax.set_ylim([0, 1.1])
        
        plt.tight_layout()
        plt.savefig('model_comparison.png', dpi=300, bbox_inches='tight')
        print("  ✓ Saved: model_comparison.png")
        plt.close()
        
        # 2. ROC curves
        fig, ax = plt.subplots(figsize=(10, 8))
        
        for name, color in zip(model_names, ['#FF6B6B', '#4ECDC4', '#FFE66D', '#95E1D3']):
            fpr, tpr, _ = roc_curve(self.y_test, self.results[name]['y_pred_proba'])
            auc = self.results[name]['roc_auc']
            ax.plot(fpr, tpr, label=f'{name} (AUC = {auc:.3f})', linewidth=2, color=color)
        
        ax.plot([0, 1], [0, 1], 'k--', linewidth=2, label='Random Classifier')
        ax.set_xlabel('False Positive Rate', fontweight='bold', fontsize=12)
        ax.set_ylabel('True Positive Rate', fontweight='bold', fontsize=12)
        ax.set_title('ROC Curves Comparison', fontweight='bold', fontsize=16, pad=20)
        ax.legend(loc='lower right')
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig('roc_curves.png', dpi=300, bbox_inches='tight')
        print("  ✓ Saved: roc_curves.png")
        plt.close()
        
        # 3. Confusion matrices
        fig, axes = plt.subplots(2, 2, figsize=(14, 12))
        axes = axes.ravel()
        
        for idx, name in enumerate(model_names):
            cm = self.results[name]['confusion_matrix']
            sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', ax=axes[idx], 
                       cbar_kws={'label': 'Count'}, square=True, linewidths=1)
            axes[idx].set_title(f'{name}\nAccuracy: {self.results[name]["accuracy"]:.4f}', 
                               fontweight='bold', fontsize=12)
            axes[idx].set_xlabel('Predicted', fontweight='bold')
            axes[idx].set_ylabel('Actual', fontweight='bold')
            axes[idx].set_xticklabels(['OFF (0)', 'ON (1)'])
            axes[idx].set_yticklabels(['OFF (0)', 'ON (1)'])
        
        plt.tight_layout()
        plt.savefig('confusion_matrices.png', dpi=300, bbox_inches='tight')
        print("  ✓ Saved: confusion_matrices.png")
        plt.close()
        
        print("\n✓ Model comparison visualizations created!")
    
    def hyperparameter_tuning(self):
        """Perform hyperparameter tuning on the best model"""
        print("\n" + "=" * 80)
        print("⚙️  HYPERPARAMETER TUNING")
        print("=" * 80)
        
        print(f"\n🔧 Tuning hyperparameters for: {self.best_model_name}")
        
        # Define parameter grids for different models
        param_grids = {
            'Decision Tree': {
                'max_depth': [5, 10, 15, 20, None],
                'min_samples_split': [2, 5, 10],
                'min_samples_leaf': [1, 2, 4],
                'criterion': ['gini', 'entropy']
            },
            'Random Forest': {
                'n_estimators': [50, 100, 200],
                'max_depth': [10, 15, 20, None],
                'min_samples_split': [2, 5],
                'min_samples_leaf': [1, 2]
            },
            'Gradient Boosting': {
                'n_estimators': [50, 100, 150],
                'learning_rate': [0.01, 0.1, 0.2],
                'max_depth': [3, 5, 7],
                'subsample': [0.8, 1.0]
            },
            'Logistic Regression': {
                'C': [0.01, 0.1, 1, 10, 100],
                'penalty': ['l2'],
                'solver': ['lbfgs', 'liblinear']
            }
        }
        
        if self.best_model_name not in param_grids:
            print(f"⚠️  No parameter grid defined for {self.best_model_name}")
            return
        
        # Get the appropriate model class
        model_classes = {
            'Decision Tree': DecisionTreeClassifier,
            'Random Forest': RandomForestClassifier,
            'Gradient Boosting': GradientBoostingClassifier,
            'Logistic Regression': LogisticRegression
        }
        
        # Prepare data
        if self.best_model_name == 'Logistic Regression':
            scaler = StandardScaler()
            X_train_prepared = scaler.fit_transform(self.X_train)
            X_test_prepared = scaler.transform(self.X_test)
        else:
            X_train_prepared = self.X_train
            X_test_prepared = self.X_test
        
        # Perform grid search
        print(f"\n🔍 Searching through parameter combinations...")
        print(f"   This may take a few minutes...")
        
        grid_search = GridSearchCV(
            model_classes[self.best_model_name](random_state=42),
            param_grids[self.best_model_name],
            cv=5,
            scoring='f1',
            n_jobs=-1,
            verbose=1
        )
        
        grid_search.fit(X_train_prepared, self.y_train)
        
        # Results
        print(f"\n✓ Hyperparameter tuning complete!")
        print(f"\n🏆 Best Parameters:")
        for param, value in grid_search.best_params_.items():
            print(f"   {param}: {value}")
        
        print(f"\n📊 Best Cross-Validation F1 Score: {grid_search.best_score_:.4f}")
        
        # Evaluate tuned model
        y_pred_tuned = grid_search.predict(X_test_prepared)
        y_pred_proba_tuned = grid_search.predict_proba(X_test_prepared)[:, 1]
        
        print(f"\n📊 Tuned Model Performance on Test Set:")
        print(f"   Accuracy:  {accuracy_score(self.y_test, y_pred_tuned):.4f}")
        print(f"   Precision: {precision_score(self.y_test, y_pred_tuned):.4f}")
        print(f"   Recall:    {recall_score(self.y_test, y_pred_tuned):.4f}")
        print(f"   F1 Score:  {f1_score(self.y_test, y_pred_tuned):.4f}")
        print(f"   ROC AUC:   {roc_auc_score(self.y_test, y_pred_proba_tuned):.4f}")
        
        # Update best model
        self.best_model = grid_search.best_estimator_
        
        print(f"\n✓ Best model updated with tuned hyperparameters!")
        
    def quantize_model(self):
        """Quantize model for embedded deployment"""
        print("\n" + "=" * 80)
        print("📦 MODEL QUANTIZATION FOR EMBEDDED DEPLOYMENT")
        print("=" * 80)
        
        print(f"\n🔧 Quantizing: {self.best_model_name}")
        
        # For tree-based models, we'll extract the decision rules
        if self.best_model_name in ['Decision Tree', 'Random Forest']:
            print("\n📋 Extracting decision tree rules...")
            
            if self.best_model_name == 'Decision Tree':
                tree_rules = export_text(self.best_model, 
                                        feature_names=['Temp', 'Humidity', 'LDR'])
                
                print("\n✓ Decision Tree Rules:")
                print(tree_rules[:500] + "..." if len(tree_rules) > 500 else tree_rules)
                
                # Save rules
                with open('decision_tree_rules.txt', 'w') as f:
                    f.write(tree_rules)
                print("\n  ✓ Saved: decision_tree_rules.txt")
                
                # Extract tree structure for C code generation
                self._export_tree_to_c_code()
                
        # For all models, create a lookup table approach
        print("\n📊 Creating quantized lookup table...")
        self._create_quantized_lookup_table()
        
        print("\n✓ Model quantization complete!")
        
    def _export_tree_to_c_code(self):
        """Export decision tree to C code for microcontroller"""
        print("\n🔧 Generating C code for microcontroller...")
        
        tree = self.best_model.tree_
        feature_names = ['temp', 'humidity', 'ldr']
        
        c_code = """/*
 * Auto-generated Decision Tree for Poultry Heater Control
 * Features: Temperature, Humidity, LDR (Light)
 * Output: Heater state (0 = OFF, 1 = ON)
 */

#include <stdint.h>

// Predict heater state based on sensor readings
uint8_t predict_heater_state(float temp, float humidity, float ldr) {
"""
        
        def recurse(node, depth):
            indent = "    " * depth
            if tree.feature[node] != -2:  # Not a leaf
                feature = feature_names[tree.feature[node]]
                threshold = tree.threshold[node]
                
                code = f"{indent}if ({feature} <= {threshold:.2f}) {{\n"
                code += recurse(tree.children_left[node], depth + 1)
                code += f"{indent}}} else {{\n"
                code += recurse(tree.children_right[node], depth + 1)
                code += f"{indent}}}\n"
                return code
            else:  # Leaf node
                # Get the class with highest count
                class_counts = tree.value[node][0]
                predicted_class = int(np.argmax(class_counts))
                return f"{indent}return {predicted_class};\n"
        
        c_code += recurse(0, 1)
        c_code += "}\n"
        
        # Save C code
        with open('heater_model.c', 'w') as f:
            f.write(c_code)
        
        print("  ✓ Saved: heater_model.c")
        
        # Also create header file
        h_code = """/*
 * Header file for Poultry Heater Control Model
 */

#ifndef HEATER_MODEL_H
#define HEATER_MODEL_H

#include <stdint.h>

// Predict heater state based on sensor readings
// Parameters:
//   temp: Temperature in Celsius
//   humidity: Humidity percentage (0-100)
//   ldr: Light intensity (0-100)
// Returns:
//   0 = Heater OFF
//   1 = Heater ON
uint8_t predict_heater_state(float temp, float humidity, float ldr);

#endif // HEATER_MODEL_H
"""
        
        with open('heater_model.h', 'w') as f:
            f.write(h_code)
        
        print("  ✓ Saved: heater_model.h")
        
    def _create_quantized_lookup_table(self):
        """Create a quantized lookup table for resource-constrained devices"""
        print("\n📊 Creating quantized lookup table...")
        
        # Create a grid of test points
        temp_range = np.arange(17, 39, 1)  # Based on data range
        humidity_range = np.arange(70, 99, 2)
        ldr_range = np.arange(0, 101, 5)
        
        # Create lookup table
        lookup_table = []
        
        for temp in temp_range:
            for humidity in humidity_range:
                for ldr in ldr_range:
                    features = np.array([[temp, humidity, ldr]])
                    
                    # Scale if needed
                    if self.best_model_name == 'Logistic Regression':
                        scaler = StandardScaler()
                        scaler.fit(self.X_train)
                        features = scaler.transform(features)
                    
                    prediction = self.best_model.predict(features)[0]
                    lookup_table.append({
                        'temp': int(temp),
                        'humidity': int(humidity),
                        'ldr': int(ldr),
                        'heater': int(prediction)
                    })
        
        # Save as JSON
        with open('lookup_table.json', 'w') as f:
            json.dump(lookup_table, f, indent=2)
        
        print(f"  ✓ Created lookup table with {len(lookup_table)} entries")
        print("  ✓ Saved: lookup_table.json")
        
        # Create a simplified version for embedded systems
        print("\n📦 Creating simplified embedded lookup table...")
        self._create_embedded_lookup_table()
        
    def _create_embedded_lookup_table(self):
        """Create a compact lookup table for embedded systems"""
        # Use coarser granularity for embedded systems
        temp_bins = np.arange(18, 38, 2)
        humidity_bins = np.arange(70, 100, 5)
        ldr_bins = np.arange(0, 101, 10)
        
        c_code = """/*
 * Compact Lookup Table for Embedded Systems
 * Uses quantized sensor values for memory efficiency
 */

#include <stdint.h>

// Quantize sensor values to bin indices
static uint8_t quantize_temp(float temp) {
    if (temp < 18) return 0;
    if (temp >= 38) return 9;
    return (uint8_t)((temp - 18) / 2);
}

static uint8_t quantize_humidity(float humidity) {
    if (humidity < 70) return 0;
    if (humidity >= 100) return 5;
    return (uint8_t)((humidity - 70) / 5);
}

static uint8_t quantize_ldr(float ldr) {
    if (ldr < 0) return 0;
    if (ldr >= 100) return 9;
    return (uint8_t)(ldr / 10);
}

// Lookup table: [temp_bin][humidity_bin][ldr_bin]
// 0 = Heater OFF, 1 = Heater ON
static const uint8_t LOOKUP_TABLE[10][6][10] = {
"""
        
        # Generate lookup table
        for t_idx, temp in enumerate(temp_bins):
            c_code += "    {\n"
            for h_idx, humidity in enumerate(humidity_bins):
                c_code += "        {"
                row = []
                for l_idx, ldr in enumerate(ldr_bins):
                    features = np.array([[temp, humidity, ldr]])
                    
                    if self.best_model_name == 'Logistic Regression':
                        scaler = StandardScaler()
                        scaler.fit(self.X_train)
                        features = scaler.transform(features)
                    
                    prediction = self.best_model.predict(features)[0]
                    row.append(str(int(prediction)))
                
                c_code += ", ".join(row)
                c_code += "}"
                if h_idx < len(humidity_bins) - 1:
                    c_code += ","
                c_code += "\n"
            c_code += "    }"
            if t_idx < len(temp_bins) - 1:
                c_code += ","
            c_code += "\n"
        
        c_code += """};

// Fast prediction using lookup table
uint8_t predict_heater_fast(float temp, float humidity, float ldr) {
    uint8_t t_bin = quantize_temp(temp);
    uint8_t h_bin = quantize_humidity(humidity);
    uint8_t l_bin = quantize_ldr(ldr);
    
    return LOOKUP_TABLE[t_bin][h_bin][l_bin];
}
"""
        
        with open('heater_model_lookup.c', 'w') as f:
            f.write(c_code)
        
        print("  ✓ Saved: heater_model_lookup.c")
        
    def save_models(self):
        """Save trained models and artifacts"""
        print("\n" + "=" * 80)
        print("💾 SAVING MODELS AND ARTIFACTS")
        print("=" * 80)
        
        # Save best model
        joblib.dump(self.best_model, 'best_model.pkl')
        print(f"\n✓ Saved best model: best_model.pkl")
        print(f"  Model: {self.best_model_name}")
        
        # Save scaler if needed
        if self.best_model_name == 'Logistic Regression':
            scaler = StandardScaler()
            scaler.fit(self.X_train)
            joblib.dump(scaler, 'scaler.pkl')
            print(f"✓ Saved scaler: scaler.pkl")
        
        # Save model metadata
        metadata = {
            'model_name': self.best_model_name,
            'features': ['Temp', 'Humidity', 'LDR'],
            'target': 'Heater',
            'performance': {
                'accuracy': float(self.results[self.best_model_name]['accuracy']),
                'precision': float(self.results[self.best_model_name]['precision']),
                'recall': float(self.results[self.best_model_name]['recall']),
                'f1_score': float(self.results[self.best_model_name]['f1']),
                'roc_auc': float(self.results[self.best_model_name]['roc_auc'])
            },
            'data_info': {
                'total_samples': len(self.df),
                'training_samples': len(self.X_train),
                'test_samples': len(self.X_test)
            }
        }
        
        with open('model_metadata.json', 'w') as f:
            json.dump(metadata, f, indent=2)
        
        print(f"✓ Saved metadata: model_metadata.json")
        
        # Create a summary report
        self._create_summary_report()
        
    def _create_summary_report(self):
        """Create a comprehensive summary report"""
        report = f"""
{'=' * 80}
SMART POULTRY HEATER CONTROL SYSTEM - ML PIPELINE SUMMARY
{'=' * 80}

📊 DATASET INFORMATION
{'─' * 80}
Total Samples:     {len(self.df):,}
Training Samples:  {len(self.X_train):,} ({len(self.X_train)/len(self.df)*100:.1f}%)
Test Samples:      {len(self.X_test):,} ({len(self.X_test)/len(self.df)*100:.1f}%)

Features:          {', '.join(['Temp', 'Humidity', 'LDR'])}
Target:            Heater (0=OFF, 1=ON)

Class Distribution:
  OFF (0): {self.df['Heater'].value_counts()[0]:,} ({self.df['Heater'].value_counts()[0]/len(self.df)*100:.2f}%)
  ON  (1): {self.df['Heater'].value_counts()[1]:,} ({self.df['Heater'].value_counts()[1]/len(self.df)*100:.2f}%)

{'─' * 80}
🤖 MODEL PERFORMANCE
{'─' * 80}
Best Model: {self.best_model_name}

Performance Metrics:
  Accuracy:  {self.results[self.best_model_name]['accuracy']:.4f}
  Precision: {self.results[self.best_model_name]['precision']:.4f}
  Recall:    {self.results[self.best_model_name]['recall']:.4f}
  F1 Score:  {self.results[self.best_model_name]['f1']:.4f}
  ROC AUC:   {self.results[self.best_model_name]['roc_auc']:.4f}

Cross-Validation:
  Mean Score: {self.results[self.best_model_name]['cv_mean']:.4f}
  Std Dev:    {self.results[self.best_model_name]['cv_std']:.4f}

Confusion Matrix:
{self.results[self.best_model_name]['confusion_matrix']}

{'─' * 80}
📦 DEPLOYMENT ARTIFACTS
{'─' * 80}
Generated Files:
  ✓ best_model.pkl              - Trained model (Python)
  ✓ model_metadata.json         - Model information
  ✓ heater_model.c              - C implementation
  ✓ heater_model.h              - C header file
  ✓ heater_model_lookup.c       - Lookup table implementation
  ✓ lookup_table.json           - Full lookup table
  ✓ decision_tree_rules.txt     - Human-readable rules

Visualizations:
  ✓ visualizations_distributions.png
  ✓ visualizations_correlation.png
  ✓ visualizations_pairplot.png
  ✓ visualizations_boxplots.png
  ✓ model_comparison.png
  ✓ roc_curves.png
  ✓ confusion_matrices.png

{'─' * 80}
💡 RECOMMENDATIONS
{'─' * 80}
1. Deploy the model using the C implementation for ESP32/ATmega328P
2. Use the lookup table for fastest inference on resource-constrained devices
3. Monitor prediction confidence and flag low-confidence cases for human review
4. Consider retraining if sensor ranges extend beyond current data
5. Implement data logging for continuous model improvement

{'=' * 80}
"""
        
        with open('ML_PIPELINE_REPORT.txt', 'w') as f:
            f.write(report)
        
        print(f"✓ Saved summary report: ML_PIPELINE_REPORT.txt")
        print(report)


def main():
    """Main execution function"""
    print("\n")
    print("╔" + "═" * 78 + "╗")
    print("║" + " " * 78 + "║")
    print("║" + "  SMART POULTRY HEATER CONTROL SYSTEM - ML PIPELINE  ".center(78) + "║")
    print("║" + " " * 78 + "║")
    print("╚" + "═" * 78 + "╝")
    print("\n")
    
    # Initialize pipeline
    pipeline = PoultryHeaterMLPipeline('data_for_IoT.csv')
    
    # Execute pipeline steps
    pipeline.load_data()
    pipeline.explore_data()
    pipeline.prepare_data()
    pipeline.train_models()
    pipeline.hyperparameter_tuning()
    pipeline.quantize_model()
    pipeline.save_models()
    
    print("\n" + "=" * 80)
    print("✅ ML PIPELINE COMPLETED SUCCESSFULLY!")
    print("=" * 80)
    print("\n🎉 All models trained, evaluated, and exported for deployment!")
    print("\n📁 Check the generated files for deployment artifacts.")
    print("\n")


if __name__ == "__main__":
    main()
