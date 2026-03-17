-- Seed default global suppliers
-- These are available to all users out of the box

INSERT INTO suppliers (name, website_url, category, is_global, is_active, reliability_score, navigation_hint)
VALUES
  ('IndiaMART',          'https://www.indiamart.com',              'general',          TRUE, TRUE, '4.2', 'Search for product, click on supplier, find Get Best Price button'),
  ('TradeIndia',         'https://www.tradeindia.com',             'general',          TRUE, TRUE, '4.0', 'Search product name, go to supplier listing, click Send Inquiry'),
  ('Udaan',              'https://udaan.com',                      'general',          TRUE, TRUE, '4.3', 'Search product, add to cart or click Get Quote'),
  ('Amazon Business IN', 'https://www.amazon.in',                  'general',          TRUE, TRUE, '4.5', 'Search product, look for bulk pricing or business discount'),
  ('Flipkart Wholesale', 'https://wholesale.flipkart.com',         'general',          TRUE, TRUE, '4.1', 'Search product category, filter by wholesale'),
  ('Robocraze',          'https://robocraze.com',                  'electronics',      TRUE, TRUE, '4.4', 'Search component name, add to cart, proceed to checkout for quote'),
  ('OfficeYes',          'https://www.officeyes.com',              'office_supplies',  TRUE, TRUE, '4.0', 'Search product, click Add to Cart or Get Quote'),
  ('Moglix',             'https://www.moglix.com',                 'industrial',       TRUE, TRUE, '4.2', 'Search product, click on item, add to quote list'),
  ('Industrybuying',     'https://www.industrybuying.com',         'industrial',       TRUE, TRUE, '4.1', 'Search product, filter category, click Request Quote'),
  ('Power2SME',          'https://www.power2sme.com',              'raw_materials',    TRUE, TRUE, '4.0', 'Register/login, search material, submit RFQ form');