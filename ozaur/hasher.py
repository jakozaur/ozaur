import random

ALPHABET = "abcdefghijklmnopqrstuwxyz0123456789"
ADDRESS_HASH_LENGTH = 40
EMAIL_HASH_LENGTH = 64

def random_address_hash():
	return "".join([random.choice(ALPHABET) for i in xrange(ADDRESS_HASH_LENGTH)])

def random_email_hash():
	return "".join([random.choice(ALPHABET) for i in xrange(EMAIL_HASH_LENGTH)])

