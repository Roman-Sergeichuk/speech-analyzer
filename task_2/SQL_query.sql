SELECT T1.date, T1.result, COUNT(T1.result) AS results_count, SUM(T1.length) AS total_length, T2.name AS project_name, T3.name AS server_name 
	FROM recordings AS T1 
	JOIN project AS T2 ON T1.project_id = T2.id 
	JOIN server AS T3 ON T1.server_id = T3.id 
	GROUP BY T1.result, T1.date, T2.name, T3.name 
	HAVING T1.date BETWEEN '2020-08-27' AND '2020-08-31' 
	ORDER BY T1.date DESC, T1.result;
