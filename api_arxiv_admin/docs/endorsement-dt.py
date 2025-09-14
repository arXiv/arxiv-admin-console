import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import matplotlib.patches as mpatches
from matplotlib.colors import LinearSegmentedColormap

plt.figure(figsize=(22, 16))

# Create a custom colormap for decision nodes (green for success, red for failure)
colors = [(0.9, 0.2, 0.2), (0.98, 0.94, 0.85), (0.2, 0.7, 0.2)]
cmap = LinearSegmentedColormap.from_list("endorsement_cmap", colors, N=100)

# Define the decision tree structure
def create_node(x, y, width, height, text, color_val=0.5, fontsize=9, fontweight='normal'):
    rect = Rectangle((x, y), width, height, facecolor=cmap(color_val), 
                    edgecolor='black', alpha=0.8)
    plt.gca().add_patch(rect)
    plt.text(x + width/2, y + height/2, text, ha='center', va='center', 
             fontsize=fontsize, fontweight=fontweight, wrap=True,
             bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="white", alpha=0.8))

# Draw connections between nodes
def connect(x1, y1, x2, y2, direction='down', color='black', label=''):
    if direction == 'down':
        plt.plot([x1, x1, x2, x2], [y1, (y1+y2)/2, (y1+y2)/2, y2], color=color)
        if label:
            plt.text((x1+x2)/2, (y1+y2)/2 + 0.1, label, ha='center', va='bottom', fontsize=8)
    elif direction == 'right':
        plt.plot([x1, (x1+x2)/2, (x1+x2)/2, x2], [y1, y1, y2, y2], color=color)
        if label:
            plt.text((x1+x2)/2, (y1+y2)/2, label, ha='center', va='bottom', fontsize=8)
    else:  # left
        plt.plot([x1, (x1+x2)/2, (x1+x2)/2, x2], [y1, y1, y2, y2], color=color)
        if label:
            plt.text((x1+x2)/2, (y1+y2)/2, label, ha='center', va='bottom', fontsize=8)

# Root node
create_node(10, 15, 4, 1, "Start can_submit()", color_val=0.5, fontsize=12, fontweight='bold')

# First level decisions
create_node(10, 13.5, 4, 0.8, "Check existing endorsement", color_val=0.5, fontsize=10)
connect(12, 15, 12, 14.3)

# Branch 1: Existing endorsement
create_node(6, 12, 4, 0.8, "Endorsement exists?", color_val=0.5, fontsize=10)
connect(12, 13.5, 8, 12.8, direction='left')
create_node(3, 10.5, 3, 0.8, "REJECT: Already submitted", color_val=0.2, fontsize=9)
create_node(9, 10.5, 3, 0.8, "Continue checks", color_val=0.5, fontsize=9)
connect(8, 12, 4.5, 11.3, label='Yes')
connect(8, 12, 10.5, 11.3, label='No')

# Branch 2: Self-endorsement check
create_node(14, 12, 4, 0.8, "Self Endorsement?", color_val=0.5, fontsize=10)
connect(12, 13.5, 16, 12.8, direction='right')
create_node(14, 10.5, 4, 0.8, "REJECT: Cannot endorse self", color_val=0.2, fontsize=9)
connect(16, 12, 16, 11.3, label='Yes')

# Branch 3: Veto status check
create_node(10, 9, 4, 0.8, "Is endorser vetoed?", color_val=0.5, fontsize=10)
connect(10.5, 10.5, 12, 9.8)
create_node(6, 7.5, 4, 0.8, "REJECT: Endorser suspended", color_val=0.2, fontsize=9)
connect(12, 9, 8, 8.3, label='Yes')

# Branch 4: Proxy submitter check
create_node(15, 7.5, 4, 0.8, "Is proxy submitter?", color_val=0.5, fontsize=10)
connect(12, 9, 17, 8.3, label='No')
create_node(15, 6, 4, 0.8, "REJECT: Proxy not allowed", color_val=0.2, fontsize=9)
connect(17, 7.5, 17, 6.8, label='Yes')

# Branch 5: Category check
create_node(10, 5, 4, 0.8, "Valid category?", color_val=0.5, fontsize=10)
connect(17, 7.5, 12, 5.8, label='No')
create_node(5, 3.5, 4, 0.8, "REJECT: Invalid category", color_val=0.2, fontsize=9)
connect(12, 5, 7, 4.3, label='No')

# Branch 6: Domain and auto-endorsement
create_node(15, 3.5, 4, 0.8, "Endorse all domain?", color_val=0.5, fontsize=10)
connect(12, 5, 17, 4.3, label='Yes')
create_node(15, 2, 4, 0.8, "ACCEPT: Auto-endorsed", color_val=0.8, fontsize=9)
connect(17, 3.5, 17, 2.8, label='Yes')

# Branch 7: Moderator check
create_node(10, 0.5, 4, 0.8, "Is endorser moderator?", color_val=0.5, fontsize=10)
connect(17, 3.5, 12, 1.3, label='No')
create_node(5, -1, 4, 0.8, "ACCEPT: Moderator status", color_val=0.8, fontsize=9)
connect(12, 0.5, 7, -0.2, label='Yes')

# Branch 8: Paper checks
create_node(15, -1, 4, 0.8, "Endorser has enough papers?", color_val=0.5, fontsize=10)
connect(12, 0.5, 17, -0.2, label='No')
create_node(15, -2.5, 4, 0.8, "ACCEPT: Sufficient papers", color_val=0.8, fontsize=9)
create_node(15, -4, 4, 0.8, "REJECT: Not enough papers", color_val=0.2, fontsize=9)
connect(17, -1, 17, -1.7, label='Yes')
connect(17, -2.5, 17, -3.2, label='No')

# Set the labels for x and y axis off
plt.axis('off')

# Add a legend
red_patch = mpatches.Patch(color=cmap(0.2), label='Rejection Node')
neutral_patch = mpatches.Patch(color=cmap(0.5), label='Decision Node')
green_patch = mpatches.Patch(color=cmap(0.8), label='Acceptance Node')
plt.legend(handles=[red_patch, neutral_patch, green_patch], loc='upper right')

# Add a title
plt.title('Decision Tree for EndorsementBusiness.can_submit() Method', fontsize=16, fontweight='bold')

# Show the plot
plt.tight_layout()
plt.show()
