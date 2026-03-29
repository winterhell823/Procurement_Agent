-- Seed default global suppliers
INSERT INTO suppliers (id, name, website, categories, is_active, is_verified, reliability_score, notes, created_at)
VALUES
  (gen_random_uuid(), 'IndiaMART', 'https://www.indiamart.com', '["general"]', TRUE, TRUE, 4.2, 'Search for product', NOW()),
  (gen_random_uuid(), 'TradeIndia', 'https://www.tradeindia.com', '["general"]', TRUE, TRUE, 4.0, 'Search product name', NOW()),
  (gen_random_uuid(), 'Udaan', 'https://udaan.com', '["general"]', TRUE, TRUE, 4.3, 'Search product', NOW()),
  (gen_random_uuid(), 'Amazon Business IN', 'https://www.amazon.in', '["general"]', TRUE, TRUE, 4.5, 'Search product', NOW()),
  (gen_random_uuid(), 'Flipkart Wholesale', 'https://wholesale.flipkart.com', '["general"]', TRUE, TRUE, 4.1, 'Search product category', NOW()),
  (gen_random_uuid(), 'Robocraze', 'https://robocraze.com', '["electronics"]', TRUE, TRUE, 4.4, 'Search component name', NOW()),
  (gen_random_uuid(), 'OfficeYes', 'https://www.officeyes.com', '["office_supplies"]', TRUE, TRUE, 4.0, 'Search product', NOW()),
  (gen_random_uuid(), 'Moglix', 'https://www.moglix.com', '["industrial"]', TRUE, TRUE, 4.2, 'Search product', NOW()),
  (gen_random_uuid(), 'Industrybuying', 'https://www.industrybuying.com', '["industrial"]', TRUE, TRUE, 4.1, 'Search product', NOW()),
  (gen_random_uuid(), 'Power2SME', 'https://www.power2sme.com', '["raw_materials"]', TRUE, TRUE, 4.0, 'Register/login', NOW());
