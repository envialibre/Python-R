import * as mysql from 'mysql2/promise';

const dbConfig = {
  host: process.env.RDS_HOST,
  user: process.env.RDS_USER,
  password: process.env.RDS_PASSWORD,
  database: process.env.RDS_DATABASE,
};

const seedDatabase = async () => {
  const connection = await mysql.createConnection(dbConfig);
  await connection.execute('INSERT INTO clients (name) VALUES (?), (?)', ['Client A', 'Client B']);
  await connection.execute('INSERT INTO requests (client_id, api_calls) VALUES (?, ?), (?, ?)', [1, 0, 2, 0]);
  await connection.end();
};

seedDatabase().catch(console.error);
