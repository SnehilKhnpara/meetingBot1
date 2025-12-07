"""Quick test to verify fixes."""
from src.participant_name_filter import is_valid_participant_name

print("Testing participant name filter:")
bad_name1 = "Backgrounds and effects"
bad_name2 = "You can't unmute someone else"
good_name1 = "John Doe"
good_name2 = "Snehil Patel"

print(f'  "{bad_name1}": {is_valid_participant_name(bad_name1)}')  # Should be False
print(f'  "{bad_name2}": {is_valid_participant_name(bad_name2)}')  # Should be False
print(f'  "{good_name1}": {is_valid_participant_name(good_name1)}')  # Should be True
print(f'  "{good_name2}": {is_valid_participant_name(good_name2)}')  # Should be True

