#Customer Branch Analysis Tool#
'''
NOTE : To run this script, do :-$ pip install jira
 			or do :-$ sudo pip install jira
'''

__author__  = 'Shubham Raj'
__credits__ = 'Madhur Raj N.'


from jira import JIRA
import requests
import csv
import random
import getpass
import datetime


def auth(server_url, username, password):
    options = {'server': server_url}
    jira = JIRA(options, basic_auth=(username,password))
    return jira


def searchissueexactmatch(jira,build,custom_field, resolution_date):
    issue = jira.search_issues(custom_field + build + ' AND resolutiondate >= '
                               + resolution_date + ' order by updated DESC')
    return issue


def searchissue(jira,subquery,build,resolution_date):
    issue = jira.search_issues('issueFunction in issueFieldMatch("","Fixed in build/s",'+ build +
                               ')' + ' AND resolutiondate >= ' + resolution_date + ' order by updated DESC', maxResults=10000)
    return issue

def searchissue_created_date(jira,subquery,build,created_date):
    issue = jira.search_issues('issueFunction in issueFieldMatch("","Fixed in build/s",'+ build +
                               ')' + ' AND createdDate >= ' + created_date + ' order by updated DESC', maxResults=10000)
    return issue

def generate_commit_info(baseUrl, issueId, username, password):
    requestlink = '/rest/dev-status/latest/issue/detail?issueId='
    requesttype = '&applicationType=stash&dataType=repository'
    link = baseUrl + requestlink + issueId + requesttype

    r = requests.get(link, auth=(username, password))

    if r.status_code == 200:
        data = r.json()
        commit_id = []
        for i in range(0, len(data['detail'][0]['repositories'])):
            for j in range(0, len(data['detail'][0]['repositories'][i]['commits'])):
                commit_id.append(data['detail'][0]['repositories'][i]['commits'][j]['displayId'])
                
        return commit_id

def generate_pr_merge_info(baseUrl,issueId,username,password):
    requestlink = '/rest/dev-status/latest/issue/detail?issueId='
    requesttype = '&applicationType=stash&dataType=pullrequest'
    link = baseUrl + requestlink + issueId +  requesttype
    r = requests.get(link, auth=(username, password))
    pr_merge_info = []
    if r.status_code == 200:
        data = r.json()
        for i in range(0, len(data['detail'][0]['pullRequests'])):
            info = []
            pr_id = data['detail'][0]['pullRequests'][i]['id']
            author = data['detail'][0]['pullRequests'][i]['author']['name']
            source = data['detail'][0]['pullRequests'][i]['source']['branch']
            destination = data['detail'][0]['pullRequests'][i]['destination']['branch']
            sourcetodestination = source +"-->"+destination 
            status = data['detail'][0]['pullRequests'][i]['status']
            info.append(pr_id)
            info.append(author)
            info.append(destination)
            #info.append(sourcetodestination)
            info.append(status)
            pr_merge_info.append(info)
        return pr_merge_info




def displayissuedetails(issue,commit_id_all,pr_merge_info_all):
    
    for i in range(0, len(issue)):
        print issue[i], " ", "Reporter :", issue[i].fields.reporter, " ", "Assignee : ", issue[i].fields.assignee
        print "Summary: ", issue[i].fields.summary
        print "Fixed in build/s: ", issue[i].fields.customfield_10300
        print "Issue Status: ",issue[i].fields.status
        print "Issue Id: ",issue[i].id
        for j in range(0,len(commit_id_all[i])):
            print "Commit id: ",commit_id_all[i][j]
        print "Total Commits:",len(commit_id_all[i])
        print ""

        for k in range(0,len(pr_merge_info_all[i])):
            print "PR id: ",pr_merge_info_all[i][k][0]
            print "PR Author: ",pr_merge_info_all[i][k][1]            
            print "Destination: ", pr_merge_info_all[i][k][2]
            print "PR Status: ", pr_merge_info_all[i][k][3]
	    print ""
        print "PR Count:",len(pr_merge_info_all[i])
        print "__________________________________________________________________________________________________"
    print "Isuue count = ",len(issue)

def datapacket_conversion(issue, commit_id_all, pr_merge_info_all):
    datapacket = [['Name', 'Summary', 'Assignee', 'Commit Id', 'PR Id','PR Author', 'PR Destination', 'PR Status', 'Merge to Main Branch(Yes/NO)','Release']]
    for i in range(0, len(issue)):
        dataframe = []
        dataframe.insert(0, issue[i].key)
        dataframe.insert(1, issue[i].fields.summary)
        dataframe.insert(2, issue[i].fields.assignee)
        dataframe.insert(3, commit_id_all[i])
        dataframe_PR_id = []
        dataframe_PR_author = []
        dataframe_merge = []
        dataframe_PR_Status = []
        for j in range(0, len(pr_merge_info_all[i])):
            dataframe_PR_id.insert(j, pr_merge_info_all[i][j][0])
            dataframe_PR_author.insert(j, pr_merge_info_all[i][j][1])
            dataframe_merge.insert(j, pr_merge_info_all[i][j][2])
            dataframe_PR_Status.insert(j, pr_merge_info_all[i][j][3])

        # Validation of whether is JIRA merged to main branch or not!!
        
        flag = 0
        branch = []
        for k in range(0, len(dataframe_merge)):
            x = dataframe_merge[k]
            status = dataframe_PR_Status[k]
            mainbranch = ['mb1','mb2','mb3','mb4','mb5']
            if x in mainbranch and status == "MERGED":
                if x not in branch:
                    branch.insert(flag,x)
                    flag += 1

        dataframe.insert(4, dataframe_PR_id)
        dataframe.insert(5, dataframe_PR_author)
        dataframe.insert(6, dataframe_merge)
        dataframe.insert(7, dataframe_PR_Status)

        if flag > 0 :
            dataframe.insert(8, 'Yes')
            dataframe.insert(9, branch)
        else:
            dataframe.insert(8, 'No')
            dataframe.insert(9, "--")

        datapacket.insert(i + 1 , dataframe)
    return datapacket

def format_datapacket(datapacket):
    temp_datapacket = datapacket
    temp_datapacket[0] = ['Name', 'Summary', 'Assignee', 'Commit Id', 'PR Info (Id : Author : Destination : Status) ',
                          'Merged to Main Branch(Yes/NO)','Release Branch']
    for i in range(1, len(temp_datapacket)):
        commit_str = ""
        for j in range(0, len(temp_datapacket[i][3])):
            commit_str += temp_datapacket[i][3][j] + '\n'
        temp_datapacket[i][3] = commit_str

    for i in range(1,len(temp_datapacket)):
        pr_info = ""
        release = ""
        for j in range(0,len(temp_datapacket[i][4])):
            pr_info_temp = temp_datapacket[i][4][j] + "  :  " + temp_datapacket[i][5][j] + "  :  " + temp_datapacket[i][6][j] + "  : " + temp_datapacket[i][7][j] + '\n'
            pr_info += pr_info_temp
        for k in range(0,len(datapacket[i][9])):
            release += datapacket[i][9][k] + '\n'

        temp_datapacket[i][4] = pr_info
        temp_datapacket[i][5] = datapacket[i][8]
        temp_datapacket[i][6] = release
        temp_datapacket[i][7] = ""
        temp_datapacket[i][8] = ""
        temp_datapacket[i][9] = ""

    return temp_datapacket


def writecsv(datapacket,build):
    dt = str(datetime.datetime.now().strftime("%y-%m-%d-%H-%M"))
    filename = "Report_" + build + "_" + dt + ".csv"
    with open(filename, 'w',) as fp:
        x = csv.writer(fp,delimiter=',')
        x.writerows(datapacket)
    print 'Filename :',filename

def main():
    baseUrl = 'https://jira.com/'
    username = raw_input('Enter your username : ')
    password = getpass.getpass("Enter Your Password : ")
    custom_field = "cf[10300] = "
    subquery = ""

    # Authentication to jira
    jira = auth(baseUrl, username, password)

    print "User logged in..."

    raw_build = raw_input('Enter Patch branch:')
    raw_build = raw_build.split('/')
    build = ""
    for i in range(0, len(raw_build)):
        build = build + raw_build[i] + "_"
    build = build[:-1]

    date = raw_input('Enter date(yyyy-mm-dd):')

    print "Extracting JIRA information ...."
    
    # 'issue' will hold info regarding all the jira while searching
    #issue = searchissue(jira,subquery,build,date)
    issue = searchissue_created_date(jira,subquery,build,date)
    print "Total issue found :",len(issue)


    # issue = searchIssueExactMatch(jira,build, custom_field, resolution_date)
    # displayIssueDetails(issue)

    print "Extracting commit and PR information ...."
    commit_id_all =[]
    pr_merge_info_all = []
    # Extracting commit and PR info for all the jira found for the build
    for i in range(0, len(issue)):
        issueid = issue[i].id
        print "Extracting Commit info for Issue :", issue[i].key
        commit_id_all.append(generate_commit_info(baseUrl, issueid, username, password))
        print "Extracting PR info for Issue :", issue[i].key
        pr_merge_info_all.append(generate_pr_merge_info(baseUrl, issueid, username, password))
	print "Count : ",i+1,"\n"
	
    displayissuedetails(issue,commit_id_all,pr_merge_info_all)
    print 'Data Packet Conversion....'
    datapacket = datapacket_conversion(issue,commit_id_all,pr_merge_info_all)
    print 'Formatting Data before writing it to CSV...'
    dataformat = format_datapacket(datapacket)
    writecsv(dataformat,build)
    print "Success"

if __name__ == "__main__":
    main()
