"""
Complete Audio Analysis Pipeline
Combines feature extraction and bluff score calculation
"""

import os
import json
from typing import Dict, List, Any, Optional
from audio_extractor import extract_features_from_wav, batch_extract_features
from bluff_calculator import calculate_bluff_score_with_baselines, simple_bluff_score

class AudioAnalyzer:
    """Main class for analyzing audio files and calculating bluff scores"""
    
    def __init__(self):
        self.features_cache = {}
        self.results_cache = {}
    
    def analyze_single_file(self, file_path: str) -> Dict[str, Any]:
        """
        Analyze a single .wav file and return features and simple bluff score
        
        Args:
            file_path: Path to the .wav file
            
        Returns:
            Dictionary with features and bluff score analysis
        """
        try:
            # Extract features
            features = extract_features_from_wav(file_path)
            self.features_cache[file_path] = features
            
            # Calculate simple bluff score
            bluff_analysis = simple_bluff_score(features)
            
            result = {
                "file_path": file_path,
                "file_name": os.path.basename(file_path),
                "features": features,
                "bluff_analysis": bluff_analysis,
                "status": "success"
            }
            
            return result
            
        except Exception as e:
            return {
                "file_path": file_path,
                "file_name": os.path.basename(file_path),
                "features": None,
                "bluff_analysis": None,
                "status": "error",
                "error": str(e)
            }
    
    def analyze_full_session(self, file_paths: List[str], question_mapping: Optional[Dict[str, int]] = None) -> Dict[str, Any]:
        """
        Analyze all 5 files from a complete session using baseline comparison
        
        Args:
            file_paths: List of paths to .wav files (should be 5 files)
            question_mapping: Optional mapping of file paths to question numbers
            
        Returns:
            Dictionary with comprehensive bluff analysis
        """
        if len(file_paths) != 5:
            return {
                "status": "error",
                "error": f"Expected 5 files for full session analysis, got {len(file_paths)}"
            }
        
        try:
            # Extract features from all files
            features_dict = batch_extract_features(file_paths)
            
            # Check if all extractions succeeded
            failed_files = [fp for fp, feats in features_dict.items() if feats is None]
            if failed_files:
                return {
                    "status": "error",
                    "error": f"Failed to extract features from: {failed_files}"
                }
            
            # Map files to questions (assume order: intro, hobby, story, technical, target)
            if question_mapping is None:
                file_list = list(file_paths)
                question_mapping = {
                    file_list[0]: 1,  # Introduction
                    file_list[1]: 2,  # Hobby
                    file_list[2]: 3,  # Story reading
                    file_list[3]: 4,  # Technical reading
                    file_list[4]: 5,  # Truth/Lie question
                }
            
            # Extract features by question type
            intro_feats = None
            hobby_feats = None
            story_feats = None
            norm_feats = None
            target_feats = None
            
            for file_path, question_num in question_mapping.items():
                feats = features_dict[file_path]
                if question_num == 1:
                    intro_feats = feats
                elif question_num == 2:
                    hobby_feats = feats
                elif question_num == 3:
                    story_feats = feats
                elif question_num == 4:
                    norm_feats = feats
                elif question_num == 5:
                    target_feats = feats
            
            # Verify we have all required features
            if None in [intro_feats, hobby_feats, story_feats, norm_feats, target_feats]:
                return {
                    "status": "error",
                    "error": "Missing features for one or more question types"
                }
            
            # Calculate advanced bluff score using baselines
            bluff_analysis = calculate_bluff_score_with_baselines(
                target_feats, intro_feats, hobby_feats, story_feats, norm_feats
            )
            
            result = {
                "status": "success",
                "session_type": "full_baseline_analysis",
                "files_analyzed": len(file_paths),
                "question_mapping": question_mapping,
                "individual_features": features_dict,
                "bluff_analysis": bluff_analysis,
                "target_features": target_feats,
                "baselines": {
                    "conversational": ["intro", "hobby"],
                    "reading": ["story", "technical"]
                }
            }
            
            return result
            
        except Exception as e:
            return {
                "status": "error",
                "error": f"Session analysis failed: {str(e)}"
            }
    
    def analyze_for_gui(self, file_paths: List[str]) -> Dict[str, Any]:
        """
        Analyze files and format results for GUI display
        
        Args:
            file_paths: List of .wav file paths
            
        Returns:
            Dictionary formatted for GUI consumption
        """
        if len(file_paths) == 5:
            # Full session analysis
            result = self.analyze_full_session(file_paths)
        elif len(file_paths) == 1:
            # Single file analysis
            result = self.analyze_single_file(file_paths[0])
        else:
            # Multiple files but not a complete session - analyze the last one as target
            target_result = self.analyze_single_file(file_paths[-1])
            result = target_result
        
        if result.get("status") != "success":
            return {
                "success": False,
                "error": result.get("error", "Analysis failed"),
                "gui_data": {
                    "bluff_score": 0,
                    "confidence": 0,
                    "reasons": ["Analysis failed"],
                    "metrics": {
                        "pause_ratio": 0,
                        "pause_count": 0,
                        "mean_f0": 0,
                        "mean_energy": 0,
                        "max_energy": 0
                    }
                }
            }
        
        # Extract bluff analysis
        if "bluff_analysis" in result:
            bluff_analysis = result["bluff_analysis"]
        else:
            bluff_analysis = {"score": 0, "confidence": 0, "reasons": ["No analysis available"]}
        
        # Extract features (from target file or single file)
        if "target_features" in result:
            features = result["target_features"]
        elif "features" in result:
            features = result["features"]
        else:
            features = {}
        
        # Convert features to GUI format
        def safe_get(key, default=0):
            return features.get(key, default) if features else default
        
        # Convert RMS dB to percentage (0-100 scale)
        mean_rms_db = safe_get("mean_rms_db", -60)
        max_rms_db = safe_get("max_rms_db", -60)
        mean_energy_pct = max(0, min(100, (mean_rms_db + 80) / 80 * 100))
        max_energy_pct = max(0, min(100, (max_rms_db + 80) / 80 * 100))
        
        gui_data = {
            "success": True,
            "bluff_score": bluff_analysis.get("score", 0),
            "confidence": bluff_analysis.get("confidence", 0),
            "reasons": bluff_analysis.get("reasons", []),
            "metrics": {
                "pause_ratio": round(safe_get("pause_ratio") * 100, 1),  # Convert to percentage
                "pause_count": safe_get("pause_count"),
                "mean_f0": safe_get("mean_f0"),
                "mean_energy": round(mean_energy_pct, 1),
                "max_energy": round(max_energy_pct, 1)
            },
            "raw_features": features,
            "analysis_detail": bluff_analysis.get("detail", {})
        }
        
        return gui_data

# Convenience functions for command-line usage
def analyze_files(file_paths: List[str]) -> Dict[str, Any]:
    """Convenience function to analyze audio files"""
    analyzer = AudioAnalyzer()
    return analyzer.analyze_for_gui(file_paths)

def analyze_and_save(file_paths: List[str], output_file: str = "analysis_results.json"):
    """Analyze files and save results to JSON"""
    results = analyze_files(file_paths)
    
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"Results saved to {output_file}")
    return results

if __name__ == "__main__":
    # Example usage
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python audio_pipeline.py <file1.wav> [file2.wav] [file3.wav] ...")
        print("       python audio_pipeline.py session1.wav session2.wav session3.wav session4.wav session5.wav")
        sys.exit(1)
    
    file_paths = sys.argv[1:]
    
    print(f"Analyzing {len(file_paths)} audio file(s)...")
    results = analyze_and_save(file_paths)
    
    if results["success"]:
        print(f"\n✅ Analysis Complete!")
        print(f"Bluff Score: {results['bluff_score']}")
        print(f"Confidence: {results['confidence']}")
        print(f"Reasons: {', '.join(results['reasons'])}")
        print(f"\nMetrics:")
        for key, value in results["metrics"].items():
            print(f"  {key}: {value}")
    else:
        print(f"\n❌ Analysis Failed: {results['error']}")