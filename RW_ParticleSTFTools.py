######## 01/04/2019 Ruby Wright --- Read Simulation Particle Data & Halo Properties ########

#*** Packages ***

if True:
    import RW_PlotParams
    import matplotlib.pyplot as plt
    import warnings
    import numpy as np
    import scipy
    import time
    import h5py

    # VELOCIraptor python tools 
    from RW_VRTools import ReadPropertyFile
    from RW_VRTools import TraceMainProgen
    from RW_VRTools import ReadHaloMergerTree
    from RW_VRTools import ReadHaloMergerTreeDescendant
    from RW_VRTools import BuildTemporalHeadTail
    from RW_VRTools import BuildTemporalHeadTailDescendant
    from RW_VRTools import ReadParticleDataFile
    from RW_VRTools import ReadSOParticleDataFile

##########################################################################################################################################################################
########################################################################### READ PARTICLE DATA ###########################################################################
##########################################################################################################################################################################

def read_swift_particle_data(run_directory,snap_no=200,part_type=[0,1],data_fields=['Coordinates','Masses','ParticleIDs','Velocities'],verbose=1):
    
    ##### inputs
    # run_directory: STRING for directory of run
    # snap_no: integer number of snaps to record from snap=0
    # parttype: LIST of INTEGER desired particle type
    # datafields: LIST of swift particle fields from ['Coordinates','Masses','ParticleIDs','Velocities']

    ##### returns
    # dictionary (snaps) of dictionaries (corresponding to each parttype) of dictionaries (corresponding to fields) -- masses in solar units, velocities in km/s, positions in Mpc
    # e.g. particle_data[snap]['PartTypeX']['field'] where X is particle type integer

    snaps=[i for i in range(snap_no)]

    #initialise list
    particle_data=[[] for i in range(snap_no)]
    
    # load hdf5 files
    particle_data_file_directories=[run_directory+"snap_"+str(snap).zfill(4)+".hdf5" for snap in snaps]
    particle_data_files=[h5py.File(particle_data_file_directories[index]) for index in range(snap_no)]

    if verbose:
        print('Saving particle data')
    
    index=0
    # loop over snaps
    for snap in snaps:
        particle_data[snap]={}
        #loop over parttypes
        for part_type_temp in part_type:
            particle_data[snap]['PartType'+str(part_type_temp)]={}

            #loop over data fields
            for field in data_fields:
                if field=='Masses':
                    particle_data[snap]['PartType'+str(part_type_temp)][field]=np.array(particle_data_files[index]['PartType'+str(part_type_temp)][field])*10**10
                else:
                    particle_data[snap]['PartType'+str(part_type_temp)][field]=np.array(particle_data_files[index]['PartType'+str(part_type_temp)][field])
        index=index+1

    if verbose:
        print('Done saving particle data')

    #return dictionary of dictionary of dictionaries
    return particle_data


# ##########################################################################################################################################################################
# ################################################################# CREATE PARTICLE ID & TYPE LIST #########################################################################
# ##########################################################################################################################################################################

# def create_particle_type_catalogue(run_directory,snap_no=200):

#     ##### inputs
#     # run_directory: STRING for directory of run

#     ##### returns
#     # dictionary of 'Particle_IDs' and 'Particle_Types'
#     # e.g. part_catalogue['Particle_IDs'] and part_catalogue['Particle_Type']
#     part_data=read_swift_particle_data(run_directory,snap_no=snap_no,part_type=[0,1],data_fields=['Coordinates','Masses','ParticleIDs','Velocities'],verbose=1)

#     print('Recording particle types for each snap')

#     part_IDs_0=[part_data[snap]['PartType0']['ParticleIDs'] for snap in range(snap_no)]#take ids at each snapshot -pt0
#     part_IDs_1=[part_data[snap]['PartType1']['ParticleIDs'] for snap in range(snap_no)]#take ids at each snapshot -pt1

#     part_catalogue=[part_IDs_0,part_IDs_1]

#     print('Finished recording particle types for each snap')

#     return(part_catalogue)

##########################################################################################################################################################################
########################################################################## CREATE HALO DATA & LINKS ######################################################################
##########################################################################################################################################################################

def read_vr_treefrog_data(vr_directory,snap_no,part_data_from_snap=120,extra_halo_fields=[],halo_TEMPORALHALOIDVAL=1000000,verbose=1):
    # reads velociraptor and treefrog outputs with desired data fields (always includes ['ID','hostHaloID','numSubStruct','Mass_tot','Mass_200crit','M_gas','Xc','Yc','Zc','R_200crit'])

    ##### inputs
    # vr_directory: STRING for directory of VELOCIRAPTOR outputs
    # snap_no: INTEGER number of snapshots in simulation (needs ALL to create merger trees etc)
    # datafields: LIST of halo data fields from VR STF output (on top of the defaults)
    # snaps: LIST of INTEGER SNAPS
    # halo_TEMPORALHALOIDVAL: from VR (default halo_TEMPORALHALOIDVAL=1000000)

    ##### returns
    # list (for each snap) of dictionaries (each field) containing field data for each halo AND concatenated particle lists for each halo

    sim_snaps=[i for i in range(snap_no)]

    extras=extra_halo_fields
    halo_fields=['ID','hostHaloID','numSubStruct','Mass_tot','Mass_200crit','M_gas','Xc','Yc','Zc','R_200crit']
    halo_fields.extend(extras)
            
    if verbose==1:
        print('Reading halo data using VR python tools')

    # Load data from all desired snaps into list structure
    halo_data_all=[ReadPropertyFile(vr_directory+'SWIFT-L25_N64-Gas-stfout-snap_'+str(snap).zfill(4),ibinary=2,iseparatesubfiles=0,iverbose=0, desiredfields=halo_fields, isiminfo=True, iunitinfo=True) for snap in sim_snaps]

    if verbose==1:
        print('Finished reading halo data')

    # List of number of halos detected for each snap, List isolated data dictionary for each snap (in dictionaries)
    halo_data_counts=[item[1] for item in halo_data_all]
    halo_data_all=[item[0] for item in halo_data_all]

    # List sim info and unit info for each snap (in dictionaries)
    halo_siminfo=[halo_data_all[snap]['SimulationInfo'] for snap in sim_snaps]
    halo_unitinfo=[halo_data_all[snap]['UnitInfo'] for snap in sim_snaps]

    # import tree data from TreeFrog, build temporal head/tails from descendants -- adds to halo_data_all (all halo data)
    if verbose==1:
        print('Assembling descendent tree using VR python tools')

    tf_treefile=vr_directory+"treefrog/listtreefiles_descen.txt"
    halo_tree=ReadHaloMergerTreeDescendant(tf_treefile,ibinary=2,iverbose=0,imerit=True,inpart=False)
    BuildTemporalHeadTailDescendant(snap_no,halo_tree,halo_data_counts,halo_data_all,iverbose=0,TEMPORALHALOIDVAL=halo_TEMPORALHALOIDVAL)

    if verbose==1:
        print('Finished assembling descendent tree using VR python tools')
    
    if verbose==1:
        print('Adding particle lists to halos using VR python tools')
    

    for snap in sim_snaps: #iterate through snaps to add particle data to halo_data_all structure

        n_halos=len(halo_data_all[snap]['ID'])

        if snap>part_data_from_snap:#if there are a good amount of halos and snap late enough
            part_data_temp=ReadParticleDataFile(vr_directory+'SWIFT-L25_N64-Gas-stfout-snap_'+str(snap).zfill(4),ibinary=2,iverbose=0,iparttypes=1)
            for part_key in list(part_data_temp.keys()):
                halo_data_all[snap][part_key]=part_data_temp[part_key]

        else:#if we don't have particle data yet
            part_data_temp={"Npart":[],"Npart_unbound":[],'Particle_IDs':[],'Particle_Type':[]}
            for part_key in list(part_data_temp.keys()):
                halo_data_all[snap][part_key]=part_data_temp[part_key] 

    if verbose==1:
        print('Finished adding particle lists to halos using VR python tools')

    if verbose==1:
        print('Appending FOF particle lists with substructure')

    for snap in sim_snaps:#iterate through snaps to add substructure particle lists to FOF halo particle

        halo_data_temp=halo_data_all[snap]
        field_halo_indices_temp=np.where(halo_data_temp['hostHaloID']==-1)[0]#find field/fof halos

        if len(field_halo_indices_temp)>0:#where there are field halos
            for field_halo_ID in halo_data_temp['ID'][field_halo_indices_temp]:#go through each field halo
                sub_halos_temp=(np.where(halo_data_temp['hostHaloID']==field_halo_ID)[0])#find its subhalos
                if len(sub_halos_temp)>0:#where there is substructure
                    field_halo_temp_index=np.where(halo_data_temp['ID']==field_halo_ID)[0][0]
                    
                    field_halo_plist=halo_data_temp['Particle_IDs'][field_halo_temp_index]
                    field_halo_tlist=halo_data_temp['Particle_Types'][field_halo_temp_index]
                    sub_halos_plist=np.concatenate([halo_data_temp['Particle_IDs'][isub] for isub in sub_halos_temp])#list all particles IDs in substructure
                    sub_halos_tlist=np.concatenate([halo_data_temp['Particle_Types'][isub] for isub in sub_halos_temp])#list all particles types substructure

                    halo_data_temp['Particle_IDs'][field_halo_temp_index]=np.concatenate([field_halo_plist,sub_halos_plist])#add particles to field halo particle list
                    halo_data_temp['Particle_Types'][field_halo_temp_index]=np.concatenate([field_halo_tlist,sub_halos_tlist])#add particles to field halo particle list
                    halo_data_temp['Npart'][field_halo_temp_index]=len(halo_data_temp['Particle_IDs'][field_halo_temp_index])#update Npart for each field halo

    if verbose==1:
        print('Finished appending FOF particle lists with substructure')

    return halo_data_all