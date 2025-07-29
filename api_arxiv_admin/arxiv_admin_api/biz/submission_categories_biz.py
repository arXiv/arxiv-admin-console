from typing import List
from sqlalchemy.orm import Session
from arxiv.db.models import Submission, SubmissionCategory

def make_submission_category_map(session, submission: Submission) -> dict:
    """Get current submission categories"""
    current_categories = session.query(SubmissionCategory).filter(
        SubmissionCategory.submission_id == submission.submission_id
    ).all()
    return {cat.category: cat for cat in current_categories}


def update_submissions_categories(session: Session, categories: List[str], submission: Submission) -> bool:
    """
    Update submission categories based on input list.
    
    Args:
        session: Database session
        categories: List of category strings (space-separated)
        submission: Submission object to update
        
    Returns:
        bool: True if any changes were made, False otherwise
        
    Categories format: space-separated list of "archive.subject_class" pairs
    First category in the list becomes the primary category.
    """
    # Parse categories from space-separated string list
    parsed_categories = []
    for cat_string in categories:
        cat_parts = cat_string.strip().split()
        parsed_categories.extend(cat_parts)
    
    # Remove duplicates while preserving order
    unique_categories = []
    seen = set()
    for cat in parsed_categories:
        if cat not in seen:
            unique_categories.append(cat)
            seen.add(cat)
    
    # Get current submission categories
    current_cat_map = make_submission_category_map(session, submission)
    
    # Categories to add/remove
    categories_to_add = set(unique_categories) - set(current_cat_map.keys())
    categories_to_remove = set(current_cat_map.keys()) - set(unique_categories)
    
    # Track if any changes were made
    changed = False
    
    # Remove categories that are no longer in the list
    for cat_to_remove in categories_to_remove:
        session.delete(current_cat_map[cat_to_remove])
        changed = True
    
    # Add new categories
    for cat_order, cat_to_add in enumerate(unique_categories):
        if cat_to_add in categories_to_add:
            new_category = SubmissionCategory(
                submission_id=submission.submission_id,
                category=cat_to_add,
                is_primary=1 if cat_order == 0 else 0,  # First category is primary
                is_published=1
            )
            session.add(new_category)
            changed = True
    
    # Update primary flag for existing categories
    for cat_order, cat_name in enumerate(unique_categories):
        if cat_name in current_cat_map:
            new_primary_value = 1 if cat_order == 0 else 0
            if current_cat_map[cat_name].is_primary != new_primary_value:
                current_cat_map[cat_name].is_primary = new_primary_value
                changed = True

    return changed
