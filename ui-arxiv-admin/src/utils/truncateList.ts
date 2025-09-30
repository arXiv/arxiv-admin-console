/**
 * Truncates a comma-separated string to show only the first n items,
 * with "and X more" appended if there are additional items.
 *
 * @param text - The comma-separated string to process
 * @param maxItems - Number of items to show before truncating (default: 3)
 * @param separator - Character to split on (default: ',')
 * @returns Truncated string or empty string if input is invalid
 */
export const truncateList = (
    text?: string | null,
    maxItems: number = 3,
    separator: string = ','
): string => {
    if (!text || text.trim() === '') {
        return '';
    }

    // Split by separator and trim whitespace from each element
    const items = text.split(separator).map(item => item.trim()).filter(item => item !== '');

    if (items.length === 0) {
        return '';
    }

    // If we have fewer items than maxItems, show all
    if (items.length <= maxItems) {
        return items.join(', ');
    }

    // Show first maxItems and indicate how many more
    const visibleItems = items.slice(0, maxItems);
    const remainingCount = items.length - maxItems;

    return `${visibleItems.join(', ')}, and ${remainingCount} more`;
};