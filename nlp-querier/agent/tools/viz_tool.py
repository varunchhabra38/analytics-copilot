from typing import Any
import matplotlib.pyplot as plt
import pandas as pd
import os

class VizTool:
    def __init__(self, output_dir: str):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    def create_visualization(self, data: pd.DataFrame, chart_type: str, title: str) -> str:
        """
        Creates a visualization based on the provided data and chart type.

        Args:
            data (pd.DataFrame): The data to visualize.
            chart_type (str): The type of chart to create (e.g., 'line', 'bar').
            title (str): The title of the chart.

        Returns:
            str: The file path of the saved visualization.
        """
        if data.empty:
            # Handle empty data
            plt.figure(figsize=(8, 6))
            plt.text(0.5, 0.5, 'No data to display', ha='center', va='center', 
                    transform=plt.gca().transAxes, fontsize=16)
            plt.title(title)
            file_path = os.path.join(self.output_dir, f"{title.replace(' ', '_').replace(':', '').lower()}.png")
            plt.savefig(file_path, bbox_inches='tight')
            plt.close()
            return file_path
        
        plt.figure(figsize=(10, 6))
        
        try:
            if chart_type == 'line':
                # For line plots, use numeric columns only
                numeric_cols = data.select_dtypes(include=['number']).columns
                if len(numeric_cols) > 0:
                    data[numeric_cols].plot(kind='line', ax=plt.gca())
                else:
                    # Fallback to simple plot
                    plt.plot(range(len(data)), [1] * len(data))
            elif chart_type == 'bar':
                # For bar charts, handle different cases
                if len(data.columns) == 1:
                    # Single column - create a simple bar chart
                    plt.bar(range(len(data)), data.iloc[:, 0])
                    plt.xticks(range(len(data)), [f"Row {i+1}" for i in range(len(data))])
                elif len(data.columns) == 2:
                    # Two columns - use first as x-axis, second as y-axis
                    col1, col2 = data.columns[0], data.columns[1]
                    plt.bar(range(len(data)), data[col2])
                    plt.xticks(range(len(data)), data[col1], rotation=45)
                else:
                    # Multiple columns - use pandas plotting
                    data.plot(kind='bar', ax=plt.gca())
                    plt.xticks(rotation=45)
            else:
                # Default fallback
                data.plot(kind='bar', ax=plt.gca())
                plt.xticks(rotation=45)
                
        except Exception as plot_error:
            # Fallback visualization on error
            plt.clf()
            plt.text(0.5, 0.5, f'Error creating visualization:\n{str(plot_error)}', 
                    ha='center', va='center', transform=plt.gca().transAxes, fontsize=12)

        plt.title(title)
        plt.xlabel(data.columns[0] if len(data.columns) > 0 else 'X-axis')
        plt.ylabel(data.columns[1] if len(data.columns) > 1 else 'Y-axis')
        plt.tight_layout()
        
        # Create safe filename
        safe_title = title.replace(' ', '_').replace(':', '').replace('/', '_').lower()
        file_path = os.path.join(self.output_dir, f"{safe_title}.png")
        
        plt.savefig(file_path, bbox_inches='tight', dpi=150)
        plt.close()
        return file_path

    def display_visualization(self, file_path: str) -> Any:
        """
        Displays the saved visualization.

        Args:
            file_path (str): The file path of the visualization to display.
        """
        img = plt.imread(file_path)
        plt.imshow(img)
        plt.axis('off')
        plt.show()